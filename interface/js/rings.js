/**
 * JARVIS V4 Multi-Axis Orbital Rings
 * Procedural concentric gyroscopic rings with tick markers, broken segments,
 * energy pulse nodes, and independent multi-axis counter-rotations.
 */

class OrbitalRings {
    constructor() {
        this.group = new THREE.Group();
        this.rings = [];
        this.time = 0;
    }

    init(scene) {
        // Ring 1: Inner equatorial tick ring (r=75)
        this.addTickRing(75, 64, 2.5, 0.0, 0.02, 0.7);

        // Ring 2: Tilted fast orbital ring (r=135)
        this.addSegmentedRing(135, Math.PI * 0.22, Math.PI * 0.15, 0.018, -0.012, 0.85);

        // Ring 3: Counter-tilted ring with markers (r=175)
        this.addTickRing(175, 48, 5.0, Math.PI * -0.32, -0.014, 0.65);

        // Ring 4: Broken multi-arc ring (r=215)
        this.addBrokenArcRing(215, Math.PI * 0.45, 0.010, 0.55);

        // Ring 5: Giant outer perimeter telemetry boundary (r=265)
        this.addOuterBoundaryRing(265, 0.004, 0.45);

        scene.add(this.group);
        console.log("[Rings] Orbital rings system initialized.");
    }

    addTickRing(radius, count, tickLength, tiltX, speedZ, opacity) {
        const ringGroup = new THREE.Group();
        ringGroup.rotation.x = tiltX;

        const points = [];
        for (let i = 0; i < count; i++) {
            const a = (i / count) * Math.PI * 2;
            const r1 = radius - tickLength * 0.5;
            const r2 = radius + tickLength * 0.5;
            points.push(new THREE.Vector3(r1 * Math.cos(a), 0, r1 * Math.sin(a)));
            points.push(new THREE.Vector3(r2 * Math.cos(a), 0, r2 * Math.sin(a)));
        }

        const geo = new THREE.BufferGeometry().setFromPoints(points);
        const mat = new THREE.LineBasicMaterial({
            color: 0xff8800,
            transparent: true,
            opacity: opacity,
            blending: THREE.AdditiveBlending
        });

        const lineSegments = new THREE.LineSegments(geo, mat);
        ringGroup.add(lineSegments);

        // Add smooth baseline circle
        const circleGeo = new THREE.BufferGeometry();
        const circlePts = [];
        for (let i = 0; i <= 100; i++) {
            const a = (i / 100) * Math.PI * 2;
            circlePts.push(new THREE.Vector3(radius * Math.cos(a), 0, radius * Math.sin(a)));
        }
        circleGeo.setFromPoints(circlePts);
        const circleMat = new THREE.LineBasicMaterial({
            color: 0xff7700,
            transparent: true,
            opacity: opacity * 0.5,
            blending: THREE.AdditiveBlending
        });
        ringGroup.add(new THREE.Line(circleGeo, circleMat));

        ringGroup.userData = { speedZ: speedZ, materials: [mat, circleMat] };
        this.rings.push(ringGroup);
        this.group.add(ringGroup);
    }

    addSegmentedRing(radius, tiltX, tiltY, speedZ, speedX, opacity) {
        const ringGroup = new THREE.Group();
        ringGroup.rotation.x = tiltX;
        ringGroup.rotation.y = tiltY;

        // Broken into 3 arc segments
        const segments = 3;
        const materials = [];
        for (let s = 0; s < segments; s++) {
            const startA = (s / segments) * Math.PI * 2 + 0.2;
            const spanA = (Math.PI * 2 / segments) - 0.5;
            const pts = [];
            const subSteps = 30;

            for (let i = 0; i <= subSteps; i++) {
                const a = startA + (i / subSteps) * spanA;
                pts.push(new THREE.Vector3(radius * Math.cos(a), 0, radius * Math.sin(a)));
            }

            const geo = new THREE.BufferGeometry().setFromPoints(pts);
            const mat = new THREE.LineBasicMaterial({
                color: 0xffaa22,
                transparent: true,
                opacity: opacity,
                blending: THREE.AdditiveBlending
            });
            materials.push(mat);
            ringGroup.add(new THREE.Line(geo, mat));
        }

        // Small glowing node travelling along the ring
        const nodeGeo = new THREE.SphereGeometry(2.8, 12, 12);
        const nodeMat = new THREE.MeshBasicMaterial({
            color: 0xffffff,
            transparent: true,
            opacity: 0.9,
            blending: THREE.AdditiveBlending
        });
        const nodeMesh = new THREE.Mesh(nodeGeo, nodeMat);
        ringGroup.add(nodeMesh);

        ringGroup.userData = {
            speedZ: speedZ,
            speedX: speedX,
            nodeMesh: nodeMesh,
            radius: radius,
            materials: materials.concat([nodeMat])
        };
        this.rings.push(ringGroup);
        this.group.add(ringGroup);
    }

    addBrokenArcRing(radius, tiltZ, speedY, opacity) {
        const ringGroup = new THREE.Group();
        ringGroup.rotation.z = tiltZ;

        const pts = [];
        const count = 70;
        const arc = Math.PI * 1.4;
        for (let i = 0; i <= count; i++) {
            const a = (i / count) * arc;
            pts.push(new THREE.Vector3(radius * Math.cos(a), radius * Math.sin(a), 0));
        }

        const geo = new THREE.BufferGeometry().setFromPoints(pts);
        const mat = new THREE.LineBasicMaterial({
            color: 0xff9900,
            transparent: true,
            opacity: opacity,
            blending: THREE.AdditiveBlending
        });

        ringGroup.add(new THREE.Line(geo, mat));
        ringGroup.userData = { speedY: speedY, materials: [mat] };
        this.rings.push(ringGroup);
        this.group.add(ringGroup);
    }

    addOuterBoundaryRing(radius, speedZ, opacity) {
        const ringGroup = new THREE.Group();
        const pts = [];
        for (let i = 0; i <= 140; i++) {
            const a = (i / 140) * Math.PI * 2;
            pts.push(new THREE.Vector3(radius * Math.cos(a), 0, radius * Math.sin(a)));
        }

        const geo = new THREE.BufferGeometry().setFromPoints(pts);
        const mat = new THREE.LineBasicMaterial({
            color: 0xff6600,
            transparent: true,
            opacity: opacity,
            blending: THREE.AdditiveBlending
        });

        ringGroup.add(new THREE.Line(geo, mat));
        ringGroup.userData = { speedZ: speedZ, materials: [mat] };
        this.rings.push(ringGroup);
        this.group.add(ringGroup);
    }

    update(delta, stateData, themeColor, audioLevels) {
        this.time += delta;
        const speed = stateData ? stateData.rotationSpeed : 1.0;
        const audioAmp = audioLevels ? audioLevels.volume * 0.4 : 0;

        this.rings.forEach((ring) => {
            const ud = ring.userData;
            if (ud.speedZ) ring.rotation.z += ud.speedZ * speed;
            if (ud.speedY) ring.rotation.y += ud.speedY * speed;
            if (ud.speedX) ring.rotation.x += ud.speedX * speed;

            // Animate travelling node if present
            if (ud.nodeMesh && ud.radius) {
                const nodeAngle = this.time * 1.8;
                ud.nodeMesh.position.set(
                    ud.radius * Math.cos(nodeAngle),
                    0,
                    ud.radius * Math.sin(nodeAngle)
                );
            }

            // Sync colors
            if (themeColor && ud.materials) {
                const threeCol = (themeColor.isColor ? themeColor : new THREE.Color(themeColor.r, themeColor.g, themeColor.b));
                ud.materials.forEach((m) => {
                    m.color.copy(threeCol);
                });
            }
        });
    }
}

window.OrbitalRings = new OrbitalRings();
