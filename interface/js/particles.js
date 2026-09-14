/**
 * JARVIS V4 GPU Particle Embers & Orbital Cloud
 * High-performance BufferGeometry particle system (up to 12,000 particles)
 * with GPU orbital drift, turbulent noise, and audio-reactive velocity.
 */

class ParticleSystem {
    constructor() {
        this.particleCount = 9000;
        this.points = null;
        this.geometry = null;
        this.material = null;
        this.uniforms = null;
        this.time = 0;
    }

    async init(scene) {
        let vertSrc = `
            attribute float aSize;
            attribute float aSpeed;
            attribute float aPhase;
            uniform float uTime;
            uniform float uAudioLevel;
            uniform float uPixelRatio;
            varying float vAlpha;
            void main() {
                float angle = uTime * aSpeed * 0.25 + aPhase;
                float cosA = cos(angle);
                float sinA = sin(angle);
                vec3 pos = position;
                float rx = pos.x * cosA - pos.z * sinA;
                float rz = pos.x * sinA + pos.z * cosA;
                pos.x = rx;
                pos.z = rz;
                float pulse = 1.0 + (sin(uTime * 3.0 + aPhase) * 0.05) + (uAudioLevel * 0.28);
                pos *= pulse;
                vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
                gl_Position = projectionMatrix * mvPosition;
                float dist = max(1.0, -mvPosition.z);
                gl_PointSize = (aSize * (1.0 + uAudioLevel * 1.6) * uPixelRatio) * (220.0 / dist);
                vAlpha = clamp(0.3 + 0.7 * sin(uTime * 2.0 + aPhase) + uAudioLevel * 0.6, 0.15, 1.0);
            }
        `;
        let fragSrc = `
            uniform vec3 uColor;
            uniform float uOpacity;
            varying float vAlpha;
            void main() {
                vec2 coord = gl_PointCoord - vec2(0.5);
                float dist = length(coord);
                if (dist > 0.5) discard;
                float glow = 1.0 - smoothstep(0.0, 0.5, dist);
                glow = pow(glow, 1.8);
                vec3 hotCenter = mix(uColor, vec3(1.0, 1.0, 0.9), glow * 0.6);
                gl_FragColor = vec4(hotCenter, glow * vAlpha * uOpacity);
            }
        `;

        try {
            const [vRes, fRes] = await Promise.all([
                fetch("shaders/particle.vert"),
                fetch("shaders/particle.frag")
            ]);
            if (vRes.ok && fRes.ok) {
                vertSrc = await vRes.text();
                fragSrc = await fRes.text();
            }
        } catch (e) {
            console.log("[Particles] Using compiled inline particle shaders.");
        }

        this.geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(this.particleCount * 3);
        const sizes = new Float32Array(this.particleCount);
        const speeds = new Float32Array(this.particleCount);
        const phases = new Float32Array(this.particleCount);

        const minR = 40;
        const maxR = 210;

        for (let i = 0; i < this.particleCount; i++) {
            // Spherical distribution with bias towards shell layers
            const u = Math.random();
            const v = Math.random();
            const theta = u * 2.0 * Math.PI;
            const phi = Math.acos(2.0 * v - 1.0);

            // Radius with layer concentrations (inner dense, shell dense, outer dispersed)
            let r;
            const rChoice = Math.random();
            if (rChoice < 0.35) {
                r = minR + Math.random() * 45; // inner mantle
            } else if (rChoice < 0.85) {
                r = 100 + Math.random() * 50; // holographic shell perimeter
            } else {
                r = 150 + Math.random() * (maxR - 150); // outer disintegration embers
            }

            const x = r * Math.sin(phi) * Math.cos(theta);
            const y = r * Math.sin(phi) * Math.sin(theta);
            const z = r * Math.cos(phi);

            positions[i * 3] = x;
            positions[i * 3 + 1] = y;
            positions[i * 3 + 2] = z;

            sizes[i] = 1.2 + Math.random() * 3.5;
            speeds[i] = (Math.random() - 0.5) * 1.5;
            phases[i] = Math.random() * Math.PI * 2;
        }

        this.geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
        this.geometry.setAttribute("aSize", new THREE.BufferAttribute(sizes, 1));
        this.geometry.setAttribute("aSpeed", new THREE.BufferAttribute(speeds, 1));
        this.geometry.setAttribute("aPhase", new THREE.BufferAttribute(phases, 1));

        this.uniforms = {
            uTime: { value: 0.0 },
            uAudioLevel: { value: 0.0 },
            uColor: { value: new THREE.Color(1.0, 0.478, 0.0) },
            uOpacity: { value: 0.95 },
            uPixelRatio: { value: Math.min(window.devicePixelRatio || 1, 2) }
        };

        this.material = new THREE.ShaderMaterial({
            vertexShader: vertSrc,
            fragmentShader: fragSrc,
            uniforms: this.uniforms,
            transparent: true,
            blending: THREE.AdditiveBlending,
            depthWrite: false
        });

        this.points = new THREE.Points(this.geometry, this.material);
        scene.add(this.points);
        console.log(`[Particles] GPU particle system initialized with ${this.particleCount} points.`);
    }

    setPerformanceLevel(level) {
        // level: "high" (9000), "medium" (5000), "low" (3000)
        let target = 9000;
        if (level === "medium") target = 5000;
        else if (level === "low") target = 3000;

        if (this.geometry) {
            this.geometry.setDrawRange(0, target);
        }
    }

    update(delta, stateData, themeColor, audioLevels) {
        this.time += delta;
        const speed = stateData ? stateData.particleActivity : 1.0;

        if (this.uniforms) {
            this.uniforms.uTime.value = this.time * speed;
            const audioVal = audioLevels ? (audioLevels.volume * 0.7 + audioLevels.treble * 0.5) : 0;
            this.uniforms.uAudioLevel.value = audioVal;

            if (themeColor) {
                const threeCol = (themeColor.isColor ? themeColor : new THREE.Color(themeColor.r, themeColor.g, themeColor.b));
                this.uniforms.uColor.value.copy(threeCol);
            }
        }

        if (this.points) {
            this.points.rotation.y += 0.0015 * speed;
            this.points.rotation.x += 0.0008 * speed;
        }
    }
}

window.ParticleSystem = new ParticleSystem();
