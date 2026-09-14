/**
 * JARVIS V4 Procedural Energy Arcs & Electric Discharges
 * Generates dynamic 3D electrical bezier arcs connecting holographic nodes
 * with wandering pulse bursts travelling across the digital sphere.
 */

class EnergyArcs {
    constructor() {
        this.group = new THREE.Group();
        this.arcs = [];
        this.time = 0;
        this.nextBurstTime = 1.0;
    }

    init(scene) {
        const arcCount = 6;
        for (let i = 0; i < arcCount; i++) {
            this.createElectricArc(i);
        }
        scene.add(this.group);
        console.log("[Arcs] Energy discharge arcs initialized.");
    }

    createElectricArc(index) {
        const radius = 105 + Math.random() * 20;
        const segmentCount = 20;
        const pts = [];

        // Generate arc between two points on the sphere
        const p1 = this.randomSpherePoint(radius);
        const p2 = this.randomSpherePoint(radius);
        const mid = p1.clone().add(p2).multiplyScalar(0.5).normalize().multiplyScalar(radius * 1.25);

        const curve = new THREE.QuadraticBezierCurve3(p1, mid, p2);
        const curvePoints = curve.getPoints(segmentCount);

        const geo = new THREE.BufferGeometry().setFromPoints(curvePoints);
        const mat = new THREE.LineBasicMaterial({
            color: 0xffbb33,
            transparent: true,
            opacity: 0.8,
            blending: THREE.AdditiveBlending
        });

        const line = new THREE.Line(geo, mat);

        // Travelling energy pulse head
        const pulseGeo = new THREE.SphereGeometry(2.0, 8, 8);
        const pulseMat = new THREE.MeshBasicMaterial({
            color: 0xffffff,
            transparent: true,
            opacity: 0.95,
            blending: THREE.AdditiveBlending
        });
        const pulseMesh = new THREE.Mesh(pulseGeo, pulseMat);
        line.add(pulseMesh);

        line.userData = {
            curve: curve,
            p1: p1,
            p2: p2,
            mid: mid,
            radius: radius,
            pulseMesh: pulseMesh,
            progress: Math.random(),
            speed: 0.8 + Math.random() * 0.8,
            life: 2.0 + Math.random() * 3.0,
            mat: mat,
            pulseMat: pulseMat
        };

        this.arcs.push(line);
        this.group.add(line);
    }

    randomSpherePoint(r) {
        const u = Math.random();
        const v = Math.random();
        const theta = u * 2.0 * Math.PI;
        const phi = Math.acos(2.0 * v - 1.0);
        return new THREE.Vector3(
            r * Math.sin(phi) * Math.cos(theta),
            r * Math.sin(phi) * Math.sin(theta),
            r * Math.cos(phi)
        );
    }

    update(delta, stateData, themeColor, audioLevels) {
        this.time += delta;
        const activity = stateData ? stateData.particleActivity : 1.0;
        const audioBoost = audioLevels ? audioLevels.treble * 1.5 : 0;

        this.arcs.forEach((line) => {
            const ud = line.userData;
            ud.progress += delta * ud.speed * (activity + audioBoost);

            if (ud.progress > 1.0) {
                ud.progress = 0.0;
                // Re-randomize arc endpoints for organic electric dancing
                ud.p1 = this.randomSpherePoint(ud.radius);
                ud.p2 = this.randomSpherePoint(ud.radius);
                ud.mid = ud.p1.clone().add(ud.p2).multiplyScalar(0.5).normalize().multiplyScalar(ud.radius * (1.15 + Math.random() * 0.25));
                ud.curve = new THREE.QuadraticBezierCurve3(ud.p1, ud.mid, ud.p2);
                line.geometry.setFromPoints(ud.curve.getPoints(20));
            }

            // Move pulse mesh along the curve
            const currentPos = ud.curve.getPoint(ud.progress);
            ud.pulseMesh.position.copy(currentPos);

            // Synchronize theme colors
            if (themeColor) {
                const threeCol = (themeColor.isColor ? themeColor : new THREE.Color(themeColor.r, themeColor.g, themeColor.b));
                ud.mat.color.copy(threeCol);
                ud.mat.opacity = 0.3 + (Math.sin(this.time * 8.0 + ud.speed) * 0.3) + (audioBoost * 0.4);
            }
        });
    }
}

window.EnergyArcs = new EnergyArcs();
