(function () {
    const payload = window.__ORCHESTRATION_MAP_PAYLOAD__;
    const canvas = document.getElementById("orchestration-map-canvas");
    if (!payload || !canvas || !(canvas instanceof HTMLCanvasElement)) {
        return;
    }

    const detailName = document.getElementById("map-detail-name");
    const detailRole = document.getElementById("map-detail-role");
    const detailTarget = document.getElementById("map-detail-target");
    const zoomOutButton = document.getElementById("map-zoom-out");
    const zoomResetButton = document.getElementById("map-zoom-reset");
    const zoomInButton = document.getElementById("map-zoom-in");
    const fullscreenButton = document.getElementById("map-fullscreen-toggle");
    const popoutLink = document.getElementById("map-popout-link");
    const mapPanel = canvas.closest(".command-map");
    const boardOverlay = document.getElementById("map-board-overlay");
    const boardOverlayBackdrop = document.getElementById("map-board-overlay-backdrop");
    const boardOverlayCloseButton = document.getElementById("map-board-overlay-close");
    const boardOverlayTitle = document.getElementById("map-board-overlay-title");
    const boardOverlayFrame = document.getElementById("map-board-overlay-frame");
    const mapCanvasWrap = canvas.closest(".command-map-canvas-wrap");

    const ctx = canvas.getContext("2d");
    if (!ctx) {
        return;
    }

    const mapWidth = Number(payload.width || 960);
    const mapHeight = Number(payload.height || 560);
    canvas.width = mapWidth;
    canvas.height = mapHeight;

    const areas = Array.isArray(payload.areas) ? payload.areas : [];
    const projectAreas = areas.filter((row) => String(row.kind || "project") === "project");
    const specialAreas = areas.filter((row) => String(row.kind || "project") !== "project");
    const spriteBasePath = String(payload.sprite_base_path || "/static/sprites/agents").replace(/\/$/, "");
    const controlUrls = payload.control_urls || {};
    const spriteVersion = String(payload.sprite_version || "20260322-sprites-v2");
    const viewState = {
        zoom: Number(payload.initial_zoom || 1),
        minZoom: 0.8,
        maxZoom: 3.4,
        panX: 0,
        panY: 0,
    };
    let fallbackFullscreenActive = false;
    let pointerDown = false;
    let draggingMap = false;
    let dragStartClientX = 0;
    let dragStartClientY = 0;
    let dragOriginPanX = 0;
    let dragOriginPanY = 0;
    let lastDragTimestamp = 0;

    function clamp(value, minValue, maxValue) {
        return Math.max(minValue, Math.min(maxValue, value));
    }

    function areaMidpoint(area) {
        return {
            x: Number(area.x) + (Number(area.width) * 0.5),
            y: Number(area.y) + (Number(area.height) * 0.5),
        };
    }

    function randomPointInArea(area) {
        const pad = 16;
        return {
            x: Number(area.x) + pad + (Math.random() * Math.max(8, Number(area.width) - (pad * 2))),
            y: Number(area.y) + pad + (Math.random() * Math.max(8, Number(area.height) - (pad * 2))),
        };
    }

    const areaById = new Map(areas.map((row) => [String(row.id), row]));
    const areaByProjectId = new Map(areas.map((row) => [String(row.project_id || ""), row]));

    function getTargetArea(agent) {
        if (agent.target_area_id && areaById.has(String(agent.target_area_id))) {
            return areaById.get(String(agent.target_area_id));
        }
        if (agent.target_project_id && areaByProjectId.has(String(agent.target_project_id))) {
            return areaByProjectId.get(String(agent.target_project_id));
        }
        return null;
    }

    function spritePathFor(agent) {
        const spriteKey = String(agent.sprite_key || agent.unit_type || "builder").toLowerCase();
        return `${spriteBasePath}/${spriteKey}`;
    }

    function loadImage(src) {
        return new Promise((resolve) => {
            const image = new Image();
            image.onload = function () {
                resolve(image);
            };
            image.onerror = function () {
                resolve(null);
            };
            image.src = src;
        });
    }

    const agents = (Array.isArray(payload.agents) ? payload.agents : []).map((rawAgent, index) => {
        const area = getTargetArea(rawAgent);
        const destination = area ? randomPointInArea(area) : {
            x: 80 + ((index % 8) * 98),
            y: 420 + ((index % 2) * 64),
        };
        return {
            id: String(rawAgent.id || `agent-${index}`),
            name: String(rawAgent.name || `Agent ${index + 1}`),
            unit_type: String(rawAgent.unit_type || "builder"),
            role: String(rawAgent.role || "member"),
            x: Number(rawAgent.x || destination.x),
            y: Number(rawAgent.y || destination.y),
            speed: Number(rawAgent.speed || 36),
            target_area_id: rawAgent.target_area_id ? String(rawAgent.target_area_id) : null,
            target_project_id: rawAgent.target_project_id ? String(rawAgent.target_project_id) : null,
            activity_state: String(rawAgent.activity_state || "idle"),
            activity_text: String(rawAgent.activity_text || ""),
            destination,
            sprite: null,
            spritePath: spritePathFor(rawAgent),
            pulse: Math.random() * Math.PI,
        };
    });

    async function loadSpriteWithFallback(basePath) {
        const extensions = [".svg", ".png"];
        for (const extension of extensions) {
            const sprite = await loadImage(`${basePath}${extension}?v=${encodeURIComponent(spriteVersion)}`);
            if (sprite) {
                return sprite;
            }
        }
        return null;
    }

    async function loadSprites() {
        const uniquePaths = Array.from(new Set(agents.map((agent) => agent.spritePath)));
        const spriteMap = new Map();
        for (const path of uniquePaths) {
            const sprite = await loadSpriteWithFallback(path);
            spriteMap.set(path, sprite);
        }
        agents.forEach((agent) => {
            agent.sprite = spriteMap.get(agent.spritePath) || null;
        });
    }

    function chooseNextDestination(agent) {
        const area = getTargetArea(agent);
        if (agent.activity_state === "killed") {
            if (area) {
                agent.destination = areaMidpoint(area);
            }
            return;
        }
        if (agent.activity_state === "sleeping") {
            if (area) {
                agent.destination = randomPointInArea(area);
            }
            return;
        }
        if (area) {
            agent.destination = randomPointInArea(area);
            return;
        }
        agent.destination = {
            x: 60 + (Math.random() * (mapWidth - 120)),
            y: 360 + (Math.random() * 160),
        };
    }

    function updateAgents(deltaSeconds) {
        for (const agent of agents) {
            if (agent.activity_state === "killed") {
                const graveArea = getTargetArea(agent);
                if (graveArea) {
                    const center = areaMidpoint(graveArea);
                    agent.x = center.x;
                    agent.y = center.y;
                }
                continue;
            }

            const dx = agent.destination.x - agent.x;
            const dy = agent.destination.y - agent.y;
            const distance = Math.sqrt((dx * dx) + (dy * dy));

            if (distance < 2) {
                chooseNextDestination(agent);
                continue;
            }

            const step = Math.min(distance, agent.speed * deltaSeconds);
            if (distance > 0) {
                agent.x += (dx / distance) * step;
                agent.y += (dy / distance) * step;
            }

            agent.x = clamp(agent.x, 18, mapWidth - 18);
            agent.y = clamp(agent.y, 18, mapHeight - 18);
            agent.pulse += deltaSeconds * 4;
        }
    }

    function areaHeatClass(area) {
        const highCount = Number(area.high_count || 0);
        if (highCount > 2) {
            return "critical";
        }
        if (highCount > 0) {
            return "warning";
        }
        return "stable";
    }

    function drawTileBackground() {
        const tileSize = 16;
        for (let y = 0; y < mapHeight; y += tileSize) {
            for (let x = 0; x < mapWidth; x += tileSize) {
                const checker = ((x / tileSize) + (y / tileSize)) % 2 === 0;
                ctx.fillStyle = checker ? "#b4d98c" : "#a5cd7d";
                ctx.fillRect(x, y, tileSize, tileSize);
            }
        }
    }

    function drawArea(area) {
        const x = Number(area.x);
        const y = Number(area.y);
        const width = Number(area.width);
        const height = Number(area.height);
        const highCount = Number(area.high_count || 0);
        const kind = String(area.kind || "project");

        if (kind === "graveyard") {
            ctx.fillStyle = "#6f7a6f";
            ctx.fillRect(x, y, width, height);
            ctx.fillStyle = "#f2f4e9";
            ctx.font = "700 11px 'Courier New', monospace";
            ctx.fillText("GRAVEYARD", x + 12, y + 16);
            for (let i = 0; i < 5; i += 1) {
                ctx.fillStyle = "#d5d6d3";
                ctx.fillRect(x + 14 + (i * 32), y + 30, 12, 18);
                ctx.fillRect(x + 12 + (i * 32), y + 34, 16, 4);
            }
            return;
        }

        if (kind === "sleep_zone") {
            ctx.fillStyle = "#c2b4df";
            ctx.fillRect(x, y, width, height);
            ctx.fillStyle = "#5f4f88";
            ctx.fillRect(x + 10, y + 8, width - 20, 26);
            ctx.fillStyle = "#ffffff";
            ctx.font = "700 11px 'Courier New', monospace";
            ctx.fillText("REST HOUSE", x + 14, y + 24);
            for (let i = 0; i < 3; i += 1) {
                ctx.fillStyle = "#efeaf8";
                ctx.fillRect(x + 18 + (i * 56), y + 52, 42, 22);
                ctx.fillStyle = "#7c6aa8";
                ctx.fillRect(x + 18 + (i * 56), y + 52, 42, 6);
            }
            return;
        }

        let fillColor = "#dfe9f8";
        let strokeColor = "#9fb4d8";
        if (highCount > 2) {
            fillColor = "#fde7ea";
            strokeColor = "#d6949f";
        } else if (highCount > 0) {
            fillColor = "#fff2d9";
            strokeColor = "#d8b17a";
        }

        ctx.fillStyle = fillColor;
        ctx.fillRect(x, y, width, height);
        ctx.strokeStyle = strokeColor;
        ctx.lineWidth = 2;
        ctx.strokeRect(x, y, width, height);

        ctx.fillStyle = "#8f5e34";
        ctx.fillRect(x + 12, y + 24, width - 24, 34);
        ctx.fillStyle = "#b57b46";
        ctx.fillRect(x + 10, y + 20, width - 20, 8);
        ctx.fillStyle = "#f0d38d";
        ctx.fillRect(x + 20, y + 32, 18, 14);
        ctx.fillRect(x + width - 38, y + 32, 18, 14);

        const deskZone = area.desk_zone || null;
        if (deskZone) {
            const deskX = Number(deskZone.x || 0);
            const deskY = Number(deskZone.y || 0);
            const deskWidth = Number(deskZone.width || 0);
            const deskHeight = Number(deskZone.height || 0);
            ctx.fillStyle = "#e4d6be";
            ctx.fillRect(deskX, deskY, deskWidth, deskHeight);
            for (let i = 0; i < 3; i += 1) {
                ctx.fillStyle = "#7f5b39";
                ctx.fillRect(deskX + 10 + (i * 54), deskY + 10, 34, 10);
            }
        }

        ctx.fillStyle = "#2e3f63";
        ctx.font = "700 11px 'Courier New', monospace";
        ctx.fillText(String(area.project_name || "Project"), x + 10, y + 18);

        ctx.fillStyle = "#536181";
        ctx.font = "10px 'Courier New', monospace";
        ctx.fillText(`q:${Number(area.open_count || 0)} h:${highCount} t:${Number(area.todo_open_count || 0)}`, x + 10, y + 72);

        const heat = areaHeatClass(area);
        const badgeColor = heat === "critical" ? "#8e1f2d" : (heat === "warning" ? "#8b5c00" : "#1f5f37");
        ctx.fillStyle = badgeColor;
        ctx.fillRect(x + width - 62, y + 8, 52, 16);
        ctx.fillStyle = "#ffffff";
        ctx.font = "700 9px 'Courier New', monospace";
        ctx.fillText(heat, x + width - 56, y + 19);
    }

    function drawRoads() {
        ctx.fillStyle = "#c6a67d";

        for (let i = 1; i <= 3; i += 1) {
            const y = 120 + (i * 120);
            ctx.fillRect(18, y - 6, mapWidth - 36, 12);
        }

        for (let i = 1; i <= 4; i += 1) {
            const x = 120 + (i * 180);
            ctx.fillRect(x - 6, 20, 12, mapHeight - 40);
        }
    }

    function drawAgent(agent, selectedAgentId) {
        const x = Math.round(agent.x);
        const y = Math.round(agent.y);
        const radius = 13;

        if (agent.sprite) {
            const spriteSize = 30;
            ctx.drawImage(agent.sprite, x - (spriteSize / 2), y - (spriteSize / 2), spriteSize, spriteSize);
        } else {
            const colorByUnitType = {
                guardian: "#2f5e96",
                builder: "#3d7a44",
                scout: "#8a6b1f",
                courier: "#6f4fb0",
            };
            ctx.fillStyle = colorByUnitType[agent.unit_type] || "#5a4f7c";
            ctx.beginPath();
            ctx.arc(x, y, radius, 0, Math.PI * 2);
            ctx.fill();
            ctx.strokeStyle = "#ffffff";
            ctx.lineWidth = 2;
            ctx.stroke();
        }

        if (selectedAgentId === agent.id) {
            ctx.strokeStyle = "#0f3b89";
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.arc(x, y, radius + 4, 0, Math.PI * 2);
            ctx.stroke();
        }

        const pulse = Math.max(0, Math.sin(agent.pulse)) * 5;
        ctx.fillStyle = "rgba(25, 62, 128, 0.15)";
        ctx.beginPath();
        ctx.ellipse(x, y + 14, radius + pulse, 6, 0, 0, Math.PI * 2);
        ctx.fill();

        if (agent.activity_state === "working") {
            ctx.fillStyle = "#ffc857";
            ctx.fillRect(x + 9, y - 16, 10, 10);
        }

        const bubbleStates = new Set(["thinking", "chatting", "working", "sleeping"]);
        if (bubbleStates.has(agent.activity_state) && agent.activity_text) {
            const label = agent.activity_text.slice(0, 18);
            ctx.fillStyle = "#ffffff";
            ctx.fillRect(x - 32, y - 33, 64, 14);
            ctx.strokeStyle = "#3c4f74";
            ctx.lineWidth = 1;
            ctx.strokeRect(x - 32, y - 33, 64, 14);
            ctx.fillStyle = "#243454";
            ctx.font = "700 8px 'Courier New', monospace";
            ctx.fillText(label, x - 29, y - 23);
        }
    }

    function drawScene(selectedAgentId) {
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        ctx.save();
        ctx.translate(viewState.panX, viewState.panY);
        ctx.scale(viewState.zoom, viewState.zoom);
        ctx.imageSmoothingEnabled = false;

        drawTileBackground();
        drawRoads();
        specialAreas.forEach((area) => drawArea(area));
        projectAreas.forEach((area) => drawArea(area));
        agents.forEach((agent) => drawAgent(agent, selectedAgentId));
        ctx.restore();
    }

    let selectedAgentId = null;

    function renderAgentDetails(agent) {
        if (!detailName || !detailRole || !detailTarget) {
            return;
        }
        if (!agent) {
            detailName.textContent = "Select an agent";
            detailRole.textContent = "Click an agent sprite on the map.";
            detailTarget.textContent = "Assignment area will appear here.";
            return;
        }

        detailName.textContent = agent.name;
        detailRole.textContent = `${agent.unit_type} | ${agent.role} | ${agent.activity_state}`;

        const area = getTargetArea(agent);
        if (area) {
            detailTarget.textContent = `Assigned to ${area.project_name} (open ${Number(area.open_count || 0)}, high ${Number(area.high_count || 0)}). ${agent.activity_text || ""}`;
        } else {
            detailTarget.textContent = "No fixed project assignment. Patrolling common town routes.";
        }
    }

    function hitTestAgent(canvasX, canvasY) {
        let closest = null;
        let closestDistance = Number.POSITIVE_INFINITY;

        for (const agent of agents) {
            const dx = canvasX - agent.x;
            const dy = canvasY - agent.y;
            const distance = Math.sqrt((dx * dx) + (dy * dy));
            if (distance <= 22 && distance < closestDistance) {
                closest = agent;
                closestDistance = distance;
            }
        }
        return closest;
    }

    function hitTestArea(canvasX, canvasY) {
        for (const area of projectAreas) {
            const x = Number(area.x || 0);
            const y = Number(area.y || 0);
            const width = Number(area.width || 0);
            const height = Number(area.height || 0);
            if (canvasX >= x && canvasX <= (x + width) && canvasY >= y && canvasY <= (y + height)) {
                return area;
            }
        }
        return null;
    }

    function toWorldCoordinates(event) {
        const rect = canvas.getBoundingClientRect();
        const screenX = (event.clientX - rect.left) * (canvas.width / rect.width);
        const screenY = (event.clientY - rect.top) * (canvas.height / rect.height);
        return {
            x: (screenX - viewState.panX) / viewState.zoom,
            y: (screenY - viewState.panY) / viewState.zoom,
            screenX,
            screenY,
        };
    }

    function clampPan() {
        const scaledWidth = mapWidth * viewState.zoom;
        const scaledHeight = mapHeight * viewState.zoom;

        if (scaledWidth <= canvas.width) {
            viewState.panX = (canvas.width - scaledWidth) * 0.5;
        } else {
            viewState.panX = clamp(viewState.panX, canvas.width - scaledWidth, 0);
        }

        if (scaledHeight <= canvas.height) {
            viewState.panY = (canvas.height - scaledHeight) * 0.5;
        } else {
            viewState.panY = clamp(viewState.panY, canvas.height - scaledHeight, 0);
        }
    }

    function updateZoomLabel() {
        if (zoomResetButton) {
            zoomResetButton.textContent = `${Math.round(viewState.zoom * 100)}%`;
        }
    }

    function setZoom(nextZoom, anchorScreenX, anchorScreenY) {
        const previousZoom = viewState.zoom;
        const clampedZoom = clamp(nextZoom, viewState.minZoom, viewState.maxZoom);
        if (Math.abs(clampedZoom - previousZoom) < 0.0001) {
            return;
        }

        const worldX = (anchorScreenX - viewState.panX) / previousZoom;
        const worldY = (anchorScreenY - viewState.panY) / previousZoom;
        viewState.zoom = clampedZoom;
        viewState.panX = anchorScreenX - (worldX * viewState.zoom);
        viewState.panY = anchorScreenY - (worldY * viewState.zoom);
        clampPan();
        updateZoomLabel();
    }

    function popoutUrl() {
        if (typeof controlUrls.popout_url === "string" && controlUrls.popout_url) {
            return controlUrls.popout_url;
        }
        if (popoutLink && popoutLink.getAttribute("href")) {
            return String(popoutLink.getAttribute("href"));
        }
        return window.location.href;
    }

    function supportsNativeFullscreen() {
        return Boolean(
            mapPanel &&
            document.fullscreenEnabled !== false &&
            typeof mapPanel.requestFullscreen === "function" &&
            typeof document.exitFullscreen === "function",
        );
    }

    function isNativeFullscreenActive() {
        return document.fullscreenElement === mapPanel;
    }

    function setFallbackFullscreen(active) {
        fallbackFullscreenActive = active;
        if (mapPanel) {
            mapPanel.classList.toggle("map-fullscreen-fallback", active);
        }
        document.body.classList.toggle("map-fullscreen-body-lock", active);
    }

    function updateFullscreenButtonState() {
        if (!fullscreenButton) {
            return;
        }
        const active = isNativeFullscreenActive() || fallbackFullscreenActive;
        fullscreenButton.textContent = active ? "Exit Fullscreen" : "Fullscreen";
        fullscreenButton.setAttribute("aria-pressed", active ? "true" : "false");
    }

    function boardOverlayUrl(area) {
        const deepLink = String(area.board_deep_link_url || "").trim();
        if (deepLink) {
            return deepLink.includes("?") ? `${deepLink}&map_mode=1` : `${deepLink}?map_mode=1`;
        }
        return String(area.board_url || "").trim();
    }

    function isBoardOverlayOpen() {
        return Boolean(boardOverlay && !boardOverlay.classList.contains("is-hidden"));
    }

    function openBoardOverlay(area) {
        const url = boardOverlayUrl(area);
        if (!url) {
            return;
        }
        if (!boardOverlay || !boardOverlayFrame) {
            window.location.href = url;
            return;
        }
        if (boardOverlayTitle) {
            boardOverlayTitle.textContent = `${String(area.project_name || "Project")} Task Board`;
        }
        boardOverlayFrame.src = url;
        boardOverlay.classList.remove("is-hidden");
        boardOverlay.setAttribute("aria-hidden", "false");
        document.body.classList.add("map-board-overlay-body-lock");
    }

    function closeBoardOverlay() {
        if (!boardOverlay || !boardOverlayFrame) {
            return;
        }
        boardOverlay.classList.add("is-hidden");
        boardOverlay.setAttribute("aria-hidden", "true");
        boardOverlayFrame.src = "about:blank";
        document.body.classList.remove("map-board-overlay-body-lock");
    }

    function isEditableTarget(target) {
        if (!(target instanceof HTMLElement)) {
            return false;
        }
        const tag = target.tagName;
        return target.isContentEditable || tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT";
    }

    function updateDragVisualState() {
        if (!mapCanvasWrap) {
            return;
        }
        mapCanvasWrap.classList.toggle("is-dragging", draggingMap);
    }

    async function requestNativeFullscreen() {
        if (!mapPanel) {
            return false;
        }
        try {
            await mapPanel.requestFullscreen();
        } catch (_error) {
            return false;
        }
        if (isNativeFullscreenActive()) {
            return true;
        }
        return false;
    }

    canvas.addEventListener("click", (event) => {
        if ((Date.now() - lastDragTimestamp) < 180) {
            return;
        }
        const world = toWorldCoordinates(event);
        const x = world.x;
        const y = world.y;

        const hitArea = hitTestArea(x, y);
        if (hitArea && hitArea.board_url) {
            openBoardOverlay(hitArea);
            return;
        }

        const hit = hitTestAgent(x, y);
        selectedAgentId = hit ? hit.id : null;
        renderAgentDetails(hit);
    });

    canvas.addEventListener("wheel", (event) => {
        event.preventDefault();
        const world = toWorldCoordinates(event);
        const zoomDelta = event.deltaY < 0 ? 1.12 : 0.9;
        setZoom(viewState.zoom * zoomDelta, world.screenX, world.screenY);
    }, { passive: false });

    canvas.addEventListener("mousedown", (event) => {
        if (event.button !== 0) {
            return;
        }
        pointerDown = true;
        draggingMap = false;
        dragStartClientX = event.clientX;
        dragStartClientY = event.clientY;
        dragOriginPanX = viewState.panX;
        dragOriginPanY = viewState.panY;
        updateDragVisualState();
    });

    document.addEventListener("mousemove", (event) => {
        if (!pointerDown) {
            return;
        }
        const rect = canvas.getBoundingClientRect();
        if (rect.width <= 0 || rect.height <= 0) {
            return;
        }
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        const dx = (event.clientX - dragStartClientX) * scaleX;
        const dy = (event.clientY - dragStartClientY) * scaleY;
        if (!draggingMap && ((Math.abs(dx) > 5) || (Math.abs(dy) > 5))) {
            draggingMap = true;
            updateDragVisualState();
        }
        if (!draggingMap) {
            return;
        }
        viewState.panX = dragOriginPanX + dx;
        viewState.panY = dragOriginPanY + dy;
        clampPan();
    });

    document.addEventListener("mouseup", () => {
        if (draggingMap) {
            lastDragTimestamp = Date.now();
        }
        pointerDown = false;
        draggingMap = false;
        updateDragVisualState();
    });

    if (boardOverlayCloseButton) {
        boardOverlayCloseButton.addEventListener("click", () => {
            closeBoardOverlay();
        });
    }

    if (boardOverlayBackdrop) {
        boardOverlayBackdrop.addEventListener("click", () => {
            closeBoardOverlay();
        });
    }

    if (zoomInButton) {
        zoomInButton.addEventListener("click", () => {
            setZoom(viewState.zoom * 1.15, canvas.width * 0.5, canvas.height * 0.5);
        });
    }
    if (zoomOutButton) {
        zoomOutButton.addEventListener("click", () => {
            setZoom(viewState.zoom * 0.88, canvas.width * 0.5, canvas.height * 0.5);
        });
    }
    if (zoomResetButton) {
        zoomResetButton.addEventListener("click", () => {
            viewState.zoom = 1;
            viewState.panX = 0;
            viewState.panY = 0;
            clampPan();
            updateZoomLabel();
        });
    }

    if (popoutLink) {
        const url = popoutUrl();
        popoutLink.setAttribute("href", url);
    }

    if (fullscreenButton && mapPanel) {
        fullscreenButton.addEventListener("click", async () => {
            if (!supportsNativeFullscreen()) {
                setFallbackFullscreen(!fallbackFullscreenActive);
                updateFullscreenButtonState();
                return;
            }

            try {
                if (!isNativeFullscreenActive()) {
                    const entered = await requestNativeFullscreen();
                    if (!entered) {
                        setFallbackFullscreen(true);
                    }
                } else {
                    await document.exitFullscreen();
                }
            } catch (_error) {
                setFallbackFullscreen(!fallbackFullscreenActive);
            }
            updateFullscreenButtonState();
        });

        document.addEventListener("fullscreenchange", () => {
            if (!document.fullscreenElement && fallbackFullscreenActive) {
                setFallbackFullscreen(false);
            }
            updateFullscreenButtonState();
        });
    }

    window.addEventListener("keydown", (event) => {
        if (isEditableTarget(event.target)) {
            return;
        }
        if (event.key === "Escape" && isBoardOverlayOpen()) {
            closeBoardOverlay();
            return;
        }
        if (event.key === "+" || event.key === "=") {
            setZoom(viewState.zoom * 1.15, canvas.width * 0.5, canvas.height * 0.5);
        }
        if (event.key === "-") {
            setZoom(viewState.zoom * 0.88, canvas.width * 0.5, canvas.height * 0.5);
        }
        if (event.key === "0") {
            viewState.zoom = 1;
            viewState.panX = 0;
            viewState.panY = 0;
            clampPan();
            updateZoomLabel();
        }
        if (event.key === "Escape" && fallbackFullscreenActive) {
            setFallbackFullscreen(false);
            updateFullscreenButtonState();
        }
        const panStep = event.shiftKey ? 120 : 56;
        if (event.key === "ArrowUp") {
            viewState.panY += panStep;
            clampPan();
        }
        if (event.key === "ArrowDown") {
            viewState.panY -= panStep;
            clampPan();
        }
        if (event.key === "ArrowLeft") {
            viewState.panX += panStep;
            clampPan();
        }
        if (event.key === "ArrowRight") {
            viewState.panX -= panStep;
            clampPan();
        }
    });

    let previousFrameTime = performance.now();
    function frame(now) {
        const deltaSeconds = Math.min(0.05, (now - previousFrameTime) / 1000);
        previousFrameTime = now;

        updateAgents(deltaSeconds);
        drawScene(selectedAgentId);
        window.requestAnimationFrame(frame);
    }

    loadSprites().then(() => {
        viewState.zoom = clamp(viewState.zoom, viewState.minZoom, viewState.maxZoom);
        clampPan();
        updateZoomLabel();
        updateFullscreenButtonState();
        drawScene(selectedAgentId);
        renderAgentDetails(null);
        window.requestAnimationFrame(frame);
    });
})();
