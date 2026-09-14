/* JARVIS V4 Layer 6: Dynamic 3D Bezier Electric Discharge Arcs */
(function(window) {
  "use strict";

  class ElectricArcs {
    constructor(parentGroup) {
      this.group = new THREE.Group();
      parentGroup.add(this.group);

      this.arcCount = 6;
      this.arcs = [];
      this.timer = 0;

      this.initArcs();
    }

    initArcs() {
      for (let i = 0; i < this.arcCount; i++) {
        const arc = this.createArc();
        this.group.add(arc.mesh);
        this.group.add(arc.pulseHead);
        this.arcs.push(arc);
      }
    }

    randomSpherical(r) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2.0 * Math.random() - 1.0);
      return new THREE.Vector3(
        r * Math.sin(phi) * Math.cos(theta),
        r * Math.sin(phi) * Math.sin(theta),
        r * Math.cos(phi)
      );
    }

    createArc() {
      const p0 = this.randomSpherical(18 + Math.random() * 10);
      const p3 = this.randomSpherical(115 + Math.random() * 25);
      
      const midR = 60 + Math.random() * 30;
      const p1 = this.randomSpherical(midR);
      const p2 = this.randomSpherical(midR);

      const curve = new THREE.CubicBezierCurve3(p0, p1, p2, p3);
      const points = curve.getPoints(24);
      const geo = new THREE.BufferGeometry().setFromPoints(points);

      const mat = new THREE.LineBasicMaterial({
        color: 0xffe0a0,
        transparent: true,
        opacity: 0.85,
        blending: THREE.AdditiveBlending
      });

      const mesh = new THREE.Line(geo, mat);

      // Pulse head (electric spark bead)
      const headGeo = new THREE.SphereGeometry(1.8, 8, 8);
      const headMat = new THREE.MeshBasicMaterial({
        color: 0xffffff,
        blending: THREE.AdditiveBlending
      });
      const pulseHead = new THREE.Mesh(headGeo, headMat);

      return {
        curve,
        mesh,
        mat,
        pulseHead,
        headMat,
        progress: Math.random(),
        speed: 0.8 + Math.random() * 1.4,
        life: 0.5 + Math.random() * 1.5
      };
    }

    rebuildArc(arc) {
      const p0 = this.randomSpherical(18 + Math.random() * 10);
      const p3 = this.randomSpherical(115 + Math.random() * 25);
      const midR = 60 + Math.random() * 30;
      const p1 = this.randomSpherical(midR);
      const p2 = this.randomSpherical(midR);

      arc.curve = new THREE.CubicBezierCurve3(p0, p1, p2, p3);
      const points = arc.curve.getPoints(24);
      arc.mesh.geometry.dispose();
      arc.mesh.geometry = new THREE.BufferGeometry().setFromPoints(points);
      arc.progress = 0;
      arc.speed = 1.0 + Math.random() * 1.8;
      arc.life = 0.4 + Math.random() * 1.2;
    }

    update(dt, audioLevel) {
      const sm = window.JarvisState ? window.JarvisState.rotMultiplier : 1.0;
      const color = window.JarvisThemes ? window.JarvisThemes.getColor() : null;

      this.arcs.forEach((arc) => {
        arc.progress += dt * arc.speed * (1.0 + audioLevel * 1.5);
        arc.life -= dt;

        if (arc.progress >= 1.0 || arc.life <= 0) {
          this.rebuildArc(arc);
        } else {
          const pt = arc.curve.getPoint(arc.progress);
          arc.pulseHead.position.copy(pt);
          arc.mat.opacity = (1.0 - arc.progress) * (0.4 + audioLevel * 0.6);
        }

        if (color) {
          arc.mat.color.copy(color);
        }
      });

      this.group.rotation.y += dt * 0.15 * sm;
    }
  }

  window.ElectricArcs = ElectricArcs;
})(window);
