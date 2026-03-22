(function () {
    const payload = window.__ORCHESTRATION_MAP_PAYLOAD__;
    const canvas = document.getElementById("orchestration-map-canvas");
    if (!payload || !canvas || !(canvas instanceof HTMLCanvasElement)) {
        return;
    }

    const detailName = document.getElementById("map-detail-name");
    const detailRole = document.getElementById("map-detail-role");
    const detailTarget = document.getElementById("map-detail-target");

    const ctx = canvas.getContext("2d");
    if (!ctx) {
        return;
    }

    const mapWidth = Number(payload.width || 960);
    const mapHeight = Number(payload.height || 560);
    canvas.width = mapWidth;
    canvas.height = mapHeight;

    const areas = Array.isArray(payload.areas) ? payload.areas : [];
    const spriteBasePath = String(payload.sprite_base_path || "/static/sprites/agents").replace(/\/$/, "");

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
            destination,
            sprite: null,
            spritePath: spritePathFor(rawAgent),
            pulse: Math.random() * Math.PI,
        };
    });

    async function loadSpriteWithFallback(basePath) {
        const extensions = [".png", ".svg"];
        for (const extension of extensions) {
            const sprite = await loadImage(`${basePath}${extension}`);
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

    function drawArea(area) {
        const x = Number(area.x);
        const y = Number(area.y);
        const width = Number(area.width);
        const height = Number(area.height);
        const highCount = Number(area.high_count || 0);

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
        ctx.strokeStyle = strokeColor;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.roundRect(x, y, width, height, 10);
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = "#2e3f63";
        ctx.font = "600 12px Georgia, serif";
        ctx.fillText(String(area.project_name || "Project"), x + 10, y + 18);

        ctx.fillStyle = "#536181";
        ctx.font = "11px Georgia, serif";
        ctx.fillText(`open ${Number(area.open_count || 0)} | high ${highCount}`, x + 10, y + 34);

        const heat = areaHeatClass(area);
        const badgeColor = heat === "critical" ? "#8e1f2d" : (heat === "warning" ? "#8b5c00" : "#1f5f37");
        ctx.fillStyle = badgeColor;
        ctx.fillRect(x + width - 62, y + 10, 52, 18);
        ctx.fillStyle = "#ffffff";
        ctx.font = "700 10px Georgia, serif";
        ctx.fillText(heat, x + width - 56, y + 22);
    }

    function drawRoads() {
        ctx.strokeStyle = "#c6d4ef";
        ctx.lineWidth = 6;
        ctx.lineCap = "round";

        for (let i = 1; i <= 3; i += 1) {
            const y = 120 + (i * 120);
            ctx.beginPath();
            ctx.moveTo(22, y);
            ctx.lineTo(mapWidth - 22, y);
            ctx.stroke();
        }

        for (let i = 1; i <= 4; i += 1) {
            const x = 120 + (i * 180);
            ctx.beginPath();
            ctx.moveTo(x, 24);
            ctx.lineTo(x, mapHeight - 24);
            ctx.stroke();
        }
    }

    function drawAgent(agent, selectedAgentId) {
        const x = Math.round(agent.x);
        const y = Math.round(agent.y);
        const radius = 13;

        if (agent.sprite) {
            const spriteSize = 28;
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
    }

    function drawScene(selectedAgentId) {
        ctx.clearRect(0, 0, mapWidth, mapHeight);

        ctx.fillStyle = "#edf3ff";
        ctx.fillRect(0, 0, mapWidth, mapHeight);

        drawRoads();
        areas.forEach((area) => drawArea(area));
        agents.forEach((agent) => drawAgent(agent, selectedAgentId));
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
        detailRole.textContent = `${agent.unit_type} | ${agent.role}`;

        const area = getTargetArea(agent);
        if (area) {
            detailTarget.textContent = `Assigned to ${area.project_name} (open ${Number(area.open_count || 0)}, high ${Number(area.high_count || 0)})`;
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

    canvas.addEventListener("click", (event) => {
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        const x = (event.clientX - rect.left) * scaleX;
        const y = (event.clientY - rect.top) * scaleY;

        const hit = hitTestAgent(x, y);
        selectedAgentId = hit ? hit.id : null;
        renderAgentDetails(hit);
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
        drawScene(selectedAgentId);
        renderAgentDetails(null);
        window.requestAnimationFrame(frame);
    });
})();
