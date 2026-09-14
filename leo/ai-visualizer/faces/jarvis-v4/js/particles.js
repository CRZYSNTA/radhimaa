/* JARVIS V4 Layer 4 & 7: 9,000+ GPU BufferGeometry Particles & Outer Embers */
(function(window) {
  "use strict";

  class ParticleCloud {
    constructor(parentGroup, vertShader, fragShader) {
      this.group = new THREE.Group();
      parentGroup.add(this.group);

      this.vertShader = vertShader;
      this.fragShader = fragShader;
      this.time = 0;
      this.count = 9200;

      this.initParticles();
    }

    initParticles() {
      const geo = new THREE.BufferGeometry();
      const positions = new Float32Array(this.count * 3);
      const sizes = new Float32Array(this.count);
      const speeds = new Float32Array(this.count);
      const phases = new Float32Array(this.count);

      for (let i = 0; i < this.count; i++) {
        // Radius clustering according to spec:
        // 35% within [40..85], 50% within [100..150], 15% within [150..210]
        let r;
        const p = Math.random();
        if (p < 0.35) {
          r = 40 + Math.random() * 45;
        } else if (p < 0.85) {
          r = 100 + Math.random() * 50;
        } else {
          r = 150 + Math.random() * 60;
        }

        // Uniform spherical distribution
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(2.0 * Math.random() - 1.0);

        positions[i * 3]     = r * Math.sin(phi) * Math.cos(theta);
        positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
        positions[i * 3 + 2] = r * Math.cos(phi);

        // Point size & orbital characteristics
        sizes[i]  = (Math.random() < 0.1 ? 4.5 : 1.8) + Math.random() * 2.2;
        speeds[i] = (Math.random() < 0.5 ? 1 : -1) * (0.3 + Math.random() * 1.2);
        phases[i] = Math.random() * Math.PI * 2;
      }

      geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      geo.setAttribute('aSize', new THREE.BufferAttribute(sizes, 1));
      geo.setAttribute('aSpeed', new THREE.BufferAttribute(speeds, 1));
      geo.setAttribute('aPhase', new THREE.BufferAttribute(phases, 1));

      this.uniforms = {
        uTime: { value: 0 },
        uAudioLevel: { value: 0 },
        uColor: { value: new THREE.Color(0xff7a00) },
        uOpacity: { value: 0.95 },
        uPixelRatio: { value: Math.min(window.devicePixelRatio, 2.0) }
      };

      this.material = new THREE.ShaderMaterial({
        vertexShader: this.vertShader,
        fragmentShader: this.fragShader,
        uniforms: this.uniforms,
        transparent: true,
        blending: THREE.AdditiveBlending,
        depthWrite: false
      });

      this.points = new THREE.Points(geo, this.material);
      this.group.add(this.points);
    }

    update(dt, audioLevel) {
      this.time += dt;
      const sm = window.JarvisState ? window.JarvisState.rotMultiplier : 1.0;

      this.uniforms.uTime.value = this.time;
      this.uniforms.uAudioLevel.value = audioLevel;
      
      // Global slow rotation
      this.points.rotation.y += dt * 0.12 * sm;
      this.points.rotation.x += dt * 0.05 * sm;

      if (window.JarvisThemes) {
        this.uniforms.uColor.value.copy(window.JarvisThemes.getColor());
      }
    }
  }

  window.ParticleCloud = ParticleCloud;
})(window);
