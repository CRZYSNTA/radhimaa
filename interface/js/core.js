/**
 * JARVIS V4 Central Holographic Core
 * Procedural multi-layer nucleus featuring inner energy source,
 * rotating geometric vortex filaments, and organic breathing pulse.
 */

class JarvisCore {
    constructor() {
        this.group = new THREE.Group();
        this.innerGlow = null;
        this.filamentsGroup = new THREE.Group();
        this.time = 0;
        
        // Multi-frequency organic breathing variables
        this.baseScale = 1.0;
        this.pulseFreq = 1.0;
        this.pulseAmp = 0.08;
    }

    init(scene) {
        // Layer 1: Bright central energy nucleus
        const coreGeo = new THREE.SphereGeometry(26, 32, 32);
        this.coreMat = new THREE.MeshBasicMaterial({
            color: 0xffa020,
            transparent: true,
            opacity: 0.95,
            blending: THREE.AdditiveBlending
        });
        this.innerGlow = new THREE.Mesh(coreGeo, this.coreMat);
        this.group.add(this.innerGlow);

        // Layer 1b: Secondary soft blooming halo
        const haloGeo = new THREE.SphereGeometry(42, 32, 32);
        this.haloMat = new THREE.MeshBasicMaterial({
            color: 0xff6600,
            transparent: true,
            opacity: 0.35,
            blending: THREE.AdditiveBlending,
            side: THREE.BackSide
        });
        this.haloMesh = new THREE.Mesh(haloGeo, this.haloMat);
        this.group.add(this.haloMesh);

        // Layer 2: Swirling geometric energy filaments / vortex spirals (from reference image)
        this.buildVortexFilaments();
        this.group.add(this.filamentsGroup);

        scene.add(this.group);
        console.log("[Core] Central holographic nucleus initialized.");
    }

    buildVortexFilaments() {
        const filamentCount = 7;
        for (let i = 0; i < filamentCount; i++) {
            const points = [];
            const turns = 2.2;
            const maxRadius = 38 + i * 4;
            const segments = 60;

            for (let s = 0; s <= segments; s++) {
                const t = s / segments;
                const angle = t * Math.PI * 2 * turns + (i * Math.PI * 2 / filamentCount);
                const r = 8 + (maxRadius - 8) * Math.pow(t, 1.2);
                const z = (Math.sin(t * Math.PI * 3) * 14) * (1 - t * 0.5);
                points.push(new THREE.Vector3(r * Math.cos(angle), r * Math.sin(angle), z));
            }

            const curve = new THREE.CatmullRomCurve3(points);
            const tubeGeo = new THREE.TubeGeometry(curve, 50, 0.7, 6, false);
            const tubeMat = new THREE.MeshBasicMaterial({
                color: 0xff8811,
                transparent: true,
                opacity: 0.75 - (i * 0.06),
                blending: THREE.AdditiveBlending
            });

            const filamentMesh = new THREE.Mesh(tubeGeo, tubeMat);
            filamentMesh.rotation.x = (i * 0.35);
            filamentMesh.rotation.y = (i * 0.45);
            filamentMesh.userData = {
                rotSpeedX: 0.015 * (i % 2 === 0 ? 1 : -1) * (1 + i * 0.1),
                rotSpeedY: 0.020 * (i % 2 === 0 ? -1 : 1) * (1 + i * 0.1)
            };
            this.filamentsGroup.add(filamentMesh);
        }
    }

    update(delta, stateData, themeColor, audioLevels) {
        this.time += delta;
        const currentSpeed = (stateData ? stateData.pulseSpeed : 1.0);

        // Multi-frequency organic breathing calculation
        const f1 = Math.sin(this.time * 2.1 * currentSpeed) * 0.5;
        const f2 = Math.cos(this.time * 1.3 * currentSpeed) * 0.3;
        const f3 = Math.sin(this.time * 0.7 * currentSpeed) * 0.2;
        const organicPulse = (f1 + f2 + f3) * this.pulseAmp;

        // Audio reactivity displacement
        const audioBoost = audioLevels ? (audioLevels.bass * 0.35 + audioLevels.volume * 0.2) : 0;
        const totalScale = this.baseScale + organicPulse + audioBoost;

        // Pulse inner nucleus independently
        if (this.innerGlow) {
            this.innerGlow.scale.set(totalScale, totalScale, totalScale);
        }
        if (this.haloMesh) {
            const haloScale = totalScale * (1.05 + Math.sin(this.time * 3.5) * 0.05);
            this.haloMesh.scale.set(haloScale, haloScale, haloScale);
        }

        // Animate filaments: counter-rotations
        this.filamentsGroup.children.forEach((mesh) => {
            const speed = (stateData ? stateData.rotationSpeed : 1.0);
            mesh.rotation.x += mesh.userData.rotSpeedX * speed;
            mesh.rotation.y += mesh.userData.rotSpeedY * speed;
            mesh.rotation.z += 0.005 * speed;
        });

        // Update colors smoothly based on active theme
        if (themeColor && this.coreMat && this.haloMat) {
            const threeCol = (themeColor.isColor ? themeColor : new THREE.Color(themeColor.r, themeColor.g, themeColor.b));
            this.coreMat.color.copy(threeCol);
            
            // Halo color slightly warmer / shifted
            const haloCol = threeCol.clone().offsetHSL(0.02, 0.1, -0.05);
            this.haloMat.color.copy(haloCol);

            this.filamentsGroup.children.forEach((m) => {
                if (m.material) {
                    m.material.color.copy(threeCol);
                }
            });

            if (window.SceneManager && window.SceneManager.corePointLight) {
                window.SceneManager.corePointLight.color.copy(threeCol);
                window.SceneManager.corePointLight.intensity = 2.5 + audioBoost * 4.0;
            }
        }
    }
}

window.JarvisCore = new JarvisCore();
