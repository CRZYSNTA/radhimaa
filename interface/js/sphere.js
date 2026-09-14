/**
 * JARVIS V4 Holographic Spherical Shell
 * Multi-layer digital globe composed of procedural GLSL noise-fractured shell,
 * segmented latitude/longitude wireframe arcs, and radial scanning bands.
 */

class HolographicSphere {
    constructor() {
        this.group = new THREE.Group();
        this.shellMesh = null;
        this.wireframeArcs = new THREE.Group();
        this.shaderUniforms = null;
        this.time = 0;
        this.radius = 110;
    }

    async init(scene) {
        // Load custom GLSL shaders or use embedded inline fallback
        let vertSrc = `
            uniform float uTime;
            uniform float uAudioLevel;
            varying vec3 vNormal;
            varying vec3 vPosition;
            varying vec3 vViewPosition;
            varying vec2 vUv;
            void main() {
                vUv = uv;
                vNormal = normalize(normalMatrix * normal);
                vPosition = position;
                float disp = sin(position.x * 4.0 + uTime * 2.0) * cos(position.y * 4.0 + uTime * 2.0) * (0.02 + uAudioLevel * 0.08);
                vec3 newPos = position + normal * disp;
                vec4 mvPosition = modelViewMatrix * vec4(newPos, 1.0);
                vViewPosition = -mvPosition.xyz;
                gl_Position = projectionMatrix * mvPosition;
            }
        `;
        let fragSrc = `
            uniform vec3 uColor;
            uniform float uTime;
            uniform float uAudioLevel;
            uniform float uOpacity;
            varying vec3 vNormal;
            varying vec3 vPosition;
            varying vec3 vViewPosition;
            varying vec2 vUv;
            float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123); }
            float noise(vec2 p) {
                vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f);
                return mix(mix(hash(i + vec2(0.0, 0.0)), hash(i + vec2(1.0, 0.0)), f.x),
                           mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x), f.y);
            }
            void main() {
                vec3 viewDir = normalize(vViewPosition);
                vec3 normal = normalize(vNormal);
                float fresnel = pow(1.0 - max(0.0, dot(viewDir, normal)), 2.5);
                float lat = fract(vUv.y * 32.0);
                float lon = fract(vUv.x * 64.0);
                float grid = step(0.92, lat) * 0.8 + step(0.94, lon) * 0.8;
                float scan = sin(vPosition.y * 5.0 - uTime * 3.0);
                scan = smoothstep(0.85, 1.0, scan);
                float n = noise(vUv * 16.0 + vec2(uTime * 0.05, 0.0));
                float digitalMask = step(0.42, n);
                float intensity = (fresnel * 1.8 + grid * 0.9 + scan * 1.5 + 0.15) * digitalMask;
                intensity += fresnel * 0.6;
                intensity *= (1.0 + uAudioLevel * 2.0);
                vec3 finalColor = uColor * intensity;
                vec3 hotGlow = mix(uColor, vec3(1.0, 0.95, 0.8), fresnel * 0.7);
                gl_FragColor = vec4(mix(finalColor, hotGlow, fresnel * 0.5), clamp(intensity * uOpacity, 0.0, 1.0));
            }
        `;

        try {
            const [vRes, fRes] = await Promise.all([
                fetch("shaders/sphere.vert"),
                fetch("shaders/sphere.frag")
            ]);
            if (vRes.ok && fRes.ok) {
                vertSrc = await vRes.text();
                fragSrc = await fRes.text();
            }
        } catch (e) {
            console.log("[Sphere] Using compiled inline shaders.");
        }

        // 1. Procedural Shader Shell
        this.shaderUniforms = {
            uTime: { value: 0.0 },
            uAudioLevel: { value: 0.0 },
            uColor: { value: new THREE.Color(1.0, 0.478, 0.0) },
            uOpacity: { value: 0.85 }
        };

        const sphereGeo = new THREE.SphereGeometry(this.radius, 64, 48);
        const shaderMat = new THREE.ShaderMaterial({
            vertexShader: vertSrc,
            fragmentShader: fragSrc,
            uniforms: this.shaderUniforms,
            transparent: true,
            blending: THREE.AdditiveBlending,
            side: THREE.DoubleSide,
            depthWrite: false
        });

        this.shellMesh = new THREE.Mesh(sphereGeo, shaderMat);
        this.group.add(this.shellMesh);

        // 2. Broken Digital Latitude & Meridian Rings
        this.buildBrokenWireframeRings();
        this.group.add(this.wireframeArcs);

        scene.add(this.group);
        console.log("[Sphere] Holographic spherical shell initialized.");
    }

    buildBrokenWireframeRings() {
        const ringCount = 8;
        for (let i = 0; i < ringCount; i++) {
            const angleDeg = -60 + i * (120 / (ringCount - 1));
            const radAngle = (angleDeg * Math.PI) / 180;
            const r = this.radius * Math.cos(radAngle);
            const y = this.radius * Math.sin(radAngle);

            // Incomplete arc with random gaps
            const segments = 48;
            const points = [];
            const arcSpan = Math.PI * (1.2 + Math.random() * 0.6);
            const startAngle = Math.random() * Math.PI * 2;

            for (let s = 0; s <= segments; s++) {
                const a = startAngle + (s / segments) * arcSpan;
                points.push(new THREE.Vector3(r * Math.cos(a), y, r * Math.sin(a)));
            }

            const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
            const lineMat = new THREE.LineBasicMaterial({
                color: 0xff8800,
                transparent: true,
                opacity: 0.4 + Math.random() * 0.35,
                blending: THREE.AdditiveBlending
            });

            const line = new THREE.Line(lineGeo, lineMat);
            line.userData = {
                rotSpeedY: 0.004 * (i % 2 === 0 ? 1 : -1) * (1 + Math.random() * 0.5)
            };
            this.wireframeArcs.add(line);
        }
    }

    update(delta, stateData, themeColor, audioLevels) {
        this.time += delta;
        const rotSpeed = stateData ? stateData.rotationSpeed : 1.0;

        // Rotate main shell
        if (this.shellMesh) {
            this.shellMesh.rotation.y += 0.005 * rotSpeed;
            this.shellMesh.rotation.x = Math.sin(this.time * 0.3) * 0.08;
        }

        // Update shader uniforms
        if (this.shaderUniforms) {
            this.shaderUniforms.uTime.value = this.time;
            const audioVal = audioLevels ? (audioLevels.mid * 0.7 + audioLevels.volume * 0.5) : 0;
            this.shaderUniforms.uAudioLevel.value = audioVal;

            if (themeColor) {
                const threeCol = (themeColor.isColor ? themeColor : new THREE.Color(themeColor.r, themeColor.g, themeColor.b));
                this.shaderUniforms.uColor.value.copy(threeCol);
            }
        }

        // Animate broken wireframe rings
        this.wireframeArcs.children.forEach((arc) => {
            arc.rotation.y += arc.userData.rotSpeedY * rotSpeed;
            if (themeColor && arc.material) {
                const threeCol = (themeColor.isColor ? themeColor : new THREE.Color(themeColor.r, themeColor.g, themeColor.b));
                arc.material.color.copy(threeCol);
            }
        });
    }
}

window.HolographicSphere = new HolographicSphere();
