/* JARVIS V4 Layer 1 & 2: Luminous Nucleus & Parametric Spiral Vortex Filaments */
(function(window) {
  "use strict";

  class HologramCore {
    constructor(parentGroup) {
      this.group = new THREE.Group();
      parentGroup.add(this.group);

      this.filaments = [];
      this.time = 0;

      this.createNucleus();
      this.createFilaments();
    }

    createNucleus() {
      // Hot inner glowing nucleus sphere
      const innerGeo = new THREE.SphereGeometry(12, 32, 32);
      this.innerMat = new THREE.MeshBasicMaterial({
        color: 0xffffff,
        transparent: true,
        opacity: 0.95,
        blending: THREE.AdditiveBlending
      });
      this.nucleusInner = new THREE.Mesh(innerGeo, this.innerMat);
      this.group.add(this.nucleusInner);

      // Mid-glow sphere
      const midGeo = new THREE.SphereGeometry(18, 32, 32);
      this.midMat = new THREE.MeshBasicMaterial({
        color: 0xff8800,
        transparent: true,
        opacity: 0.65,
        blending: THREE.AdditiveBlending,
        wireframe: false
      });
      this.nucleusMid = new THREE.Mesh(midGeo, this.midMat);
      this.group.add(this.nucleusMid);

      // Outer wireframe energy halo
      const outerGeo = new THREE.IcosahedronGeometry(24, 2);
      this.outerMat = new THREE.MeshBasicMaterial({
        color: 0xffaa00,
        wireframe: true,
        transparent: true,
        opacity: 0.45,
        blending: THREE.AdditiveBlending
      });
      this.nucleusOuter = new THREE.Mesh(outerGeo, this.outerMat);
      this.group.add(this.nucleusOuter);
    }

    createFilaments() {
      const filamentCount = 7;
      this.filamentGroup = new THREE.Group();
      this.group.add(this.filamentGroup);

      for (let i = 0; i < filamentCount; i++) {
        const points = [];
        const turns = 2.2;
        const maxRadius = 38 + i * 4.5;
        const segments = 64;

        for (let s = 0; s <= segments; s++) {
          const t = s / segments;
          const angle = t * Math.PI * 2 * turns + (i * Math.PI * 2 / filamentCount);
          const r = 8 + (maxRadius - 8) * Math.pow(t, 1.25);
          const z = (Math.sin(t * Math.PI * 3.2) * 14) * (1 - t * 0.45);
          points.push(new THREE.Vector3(r * Math.cos(angle), r * Math.sin(angle), z));
        }

        const curve = new THREE.CatmullRomCurve3(points);
        const tubeGeo = new THREE.TubeGeometry(curve, 54, 0.75, 6, false);
        
        const mat = new THREE.MeshBasicMaterial({
          color: 0xffa020,
          transparent: true,
          opacity: 0.75,
          blending: THREE.AdditiveBlending,
          wireframe: i % 2 === 1
        });

        const mesh = new THREE.Mesh(tubeGeo, mat);
        mesh.userData = {
          rotSpeed: (i % 2 === 0 ? 1 : -1) * (0.8 + (i * 0.15)),
          tiltX: (i * 0.18),
          tiltY: (i * 0.24)
        };
        mesh.rotation.x = mesh.userData.tiltX;
        mesh.rotation.y = mesh.userData.tiltY;

        this.filamentGroup.add(mesh);
        this.filaments.push(mesh);
      }
    }

    update(dt, audioLevel) {
      this.time += dt;

      const stateMultiplier = window.JarvisState ? window.JarvisState.rotMultiplier : 1.0;
      const pulseMultiplier = window.JarvisState ? window.JarvisState.pulseMultiplier : 1.0;

      // Nucleus breathing & audio scaling
      const breath = 1.0 + Math.sin(this.time * 2.5 * pulseMultiplier) * 0.08 + (audioLevel * 0.45);
      this.nucleusInner.scale.set(breath, breath, breath);
      this.nucleusMid.scale.set(breath * 1.15, breath * 1.15, breath * 1.15);
      this.nucleusOuter.scale.set(breath * 1.3, breath * 1.3, breath * 1.3);

      this.nucleusOuter.rotation.x += dt * 0.4 * stateMultiplier;
      this.nucleusOuter.rotation.y += dt * 0.6 * stateMultiplier;

      // Rotate spiral vortex filaments
      this.filamentGroup.rotation.z += dt * 0.6 * stateMultiplier;
      this.filaments.forEach((mesh) => {
        mesh.rotation.z += dt * mesh.userData.rotSpeed * stateMultiplier;
        const s = 1.0 + Math.sin(this.time * 3.0 + mesh.userData.tiltX) * 0.05 + audioLevel * 0.2;
        mesh.scale.set(s, s, s);
      });

      // Synchronize color
      if (window.JarvisThemes) {
        const c = window.JarvisThemes.getColor();
        this.midMat.color.copy(c);
        this.outerMat.color.copy(c);
        this.filaments.forEach(f => f.material.color.copy(c));
      }
    }
  }

  window.HologramCore = HologramCore;
})(window);
