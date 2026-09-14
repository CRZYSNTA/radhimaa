/* JARVIS V4 Layer 3: 5 Multi-Axis Counter-Rotating Orbital Rings with Ticks */
(function(window) {
  "use strict";

  class OrbitalRings {
    constructor(parentGroup) {
      this.group = new THREE.Group();
      parentGroup.add(this.group);

      this.rings = [];
      this.time = 0;

      this.initRings();
    }

    initRings() {
      // Ring 1: Inner Equatorial Tick Ring (r=75)
      this.ring1 = this.createTickRing(75, 48, 4.0, 0.9);
      this.ring1.userData = { speedX: 0.1, speedY: 0.25, speedZ: 0.35 };
      this.group.add(this.ring1);
      this.rings.push(this.ring1);

      // Ring 2: Segmented Arc Ring with Pulse Node (r=135, tiltX=0.22pi, tiltY=0.15pi)
      this.ring2 = this.createSegmentedRing(135, 3, 0.85);
      this.ring2.rotation.x = Math.PI * 0.22;
      this.ring2.rotation.y = Math.PI * 0.15;
      this.ring2.userData = { speedX: 0.05, speedY: -0.3, speedZ: 0.2 };
      
      // Traveling pulse bead on Ring 2
      const beadGeo = new THREE.SphereGeometry(2.5, 12, 12);
      const beadMat = new THREE.MeshBasicMaterial({
        color: 0xffffff,
        blending: THREE.AdditiveBlending
      });
      this.pulseBead = new THREE.Mesh(beadGeo, beadMat);
      this.ring2.add(this.pulseBead);

      this.group.add(this.ring2);
      this.rings.push(this.ring2);

      // Ring 3: Counter-Tilted Tick Ring (r=175, tiltX=-0.32pi)
      this.ring3 = this.createTickRing(175, 64, 5.5, 0.75);
      this.ring3.rotation.x = -Math.PI * 0.32;
      this.ring3.userData = { speedX: -0.15, speedY: 0.2, speedZ: -0.25 };
      this.group.add(this.ring3);
      this.rings.push(this.ring3);

      // Ring 4: Broken Multi-Arc Ring (r=215, tiltZ=0.45pi)
      this.ring4 = this.createSegmentedRing(215, 6, 0.65);
      this.ring4.rotation.z = Math.PI * 0.45;
      this.ring4.userData = { speedX: 0.2, speedY: -0.1, speedZ: 0.18 };
      this.group.add(this.ring4);
      this.rings.push(this.ring4);

      // Ring 5: Outer Perimeter Telemetry Boundary Ring (r=265)
      this.ring5 = this.createBoundaryRing(265);
      this.ring5.userData = { speedX: 0.02, speedY: 0.04, speedZ: -0.08 };
      this.group.add(this.ring5);
      this.rings.push(this.ring5);
    }

    createTickRing(radius, count, tickLen, opacity) {
      const group = new THREE.Group();
      
      // Main circle line
      const circleGeo = new THREE.BufferGeometry();
      const circlePts = [];
      const segs = 120;
      for (let i = 0; i <= segs; i++) {
        const theta = (i / segs) * Math.PI * 2;
        circlePts.push(radius * Math.cos(theta), radius * Math.sin(theta), 0);
      }
      circleGeo.setAttribute('position', new THREE.Float32BufferAttribute(circlePts, 3));
      const circleMat = new THREE.LineBasicMaterial({
        color: 0xff8800,
        transparent: true,
        opacity: opacity * 0.7,
        blending: THREE.AdditiveBlending
      });
      group.add(new THREE.Line(circleGeo, circleMat));

      // Radial ticks
      const tickGeo = new THREE.BufferGeometry();
      const tickPts = [];
      for (let i = 0; i < count; i++) {
        const theta = (i / count) * Math.PI * 2;
        const cos = Math.cos(theta);
        const sin = Math.sin(theta);
        const r1 = radius - tickLen * 0.5;
        const r2 = radius + tickLen * 0.5;
        tickPts.push(r1 * cos, r1 * sin, 0);
        tickPts.push(r2 * cos, r2 * sin, 0);
      }
      tickGeo.setAttribute('position', new THREE.Float32BufferAttribute(tickPts, 3));
      const tickMat = new THREE.LineSegments(tickGeo, new THREE.LineBasicMaterial({
        color: 0xffaa00,
        transparent: true,
        opacity: opacity,
        blending: THREE.AdditiveBlending
      }));
      group.add(tickMat);

      group.userData.mats = [circleMat, tickMat.material];
      return group;
    }

    createSegmentedRing(radius, arcsCount, opacity) {
      const group = new THREE.Group();
      const mats = [];

      for (let i = 0; i < arcsCount; i++) {
        const start = (i / arcsCount) * Math.PI * 2;
        const span = (Math.PI * 2 / arcsCount) * 0.68;
        const segs = 32;
        const pts = [];

        for (let j = 0; j <= segs; j++) {
          const theta = start + (j / segs) * span;
          pts.push(radius * Math.cos(theta), radius * Math.sin(theta), 0);
        }

        const geo = new THREE.BufferGeometry();
        geo.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
        const mat = new THREE.LineBasicMaterial({
          color: 0xff9900,
          transparent: true,
          opacity: opacity,
          linewidth: 1.5,
          blending: THREE.AdditiveBlending
        });
        mats.push(mat);
        group.add(new THREE.Line(geo, mat));
      }

      group.userData.mats = mats;
      return group;
    }

    createBoundaryRing(radius) {
      const group = new THREE.Group();
      const geo = new THREE.BufferGeometry();
      const pts = [];
      const segs = 144;
      for (let i = 0; i <= segs; i++) {
        const theta = (i / segs) * Math.PI * 2;
        pts.push(radius * Math.cos(theta), radius * Math.sin(theta), 0);
      }
      geo.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3));
      const mat = new THREE.LineBasicMaterial({
        color: 0xcc6600,
        transparent: true,
        opacity: 0.35,
        blending: THREE.AdditiveBlending
      });
      group.add(new THREE.Line(geo, mat));
      group.userData.mats = [mat];
      return group;
    }

    update(dt, audioLevel) {
      this.time += dt;
      const sm = window.JarvisState ? window.JarvisState.rotMultiplier : 1.0;

      this.rings.forEach((ring) => {
        ring.rotation.x += dt * ring.userData.speedX * sm;
        ring.rotation.y += dt * ring.userData.speedY * sm;
        ring.rotation.z += dt * ring.userData.speedZ * sm;

        // Subtle audio pulse expansion
        const s = 1.0 + audioLevel * 0.05;
        ring.scale.set(s, s, s);
      });

      // Move traveling pulse bead along Ring 2
      const beadAngle = this.time * 2.5 * sm;
      this.pulseBead.position.set(
        135 * Math.cos(beadAngle),
        135 * Math.sin(beadAngle),
        0
      );

      // Theme color update
      if (window.JarvisThemes) {
        const c = window.JarvisThemes.getColor();
        this.rings.forEach(ring => {
          if (ring.userData.mats) {
            ring.userData.mats.forEach(m => m.color.copy(c));
          }
        });
      }
    }
  }

  window.OrbitalRings = OrbitalRings;
})(window);
