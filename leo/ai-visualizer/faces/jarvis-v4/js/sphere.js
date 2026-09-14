/* JARVIS V4 Layer 5: Procedural GLSL Fractured Noise Sphere & Wireframe Shell */
(function(window) {
  "use strict";

  class FracturedSphere {
    constructor(parentGroup, vertShader, fragShader) {
      this.group = new THREE.Group();
      parentGroup.add(this.group);

      this.vertShader = vertShader;
      this.fragShader = fragShader;
      this.time = 0;

      this.initSphere();
      this.initWireframeShell();
    }

    initSphere() {
      const geo = new THREE.SphereGeometry(125, 64, 64);
      
      this.uniforms = {
        uTime: { value: 0 },
        uAudioLevel: { value: 0 },
        uColor: { value: new THREE.Color(0xff7a00) },
        uOpacity: { value: 0.85 }
      };

      this.material = new THREE.ShaderMaterial({
        vertexShader: this.vertShader,
        fragmentShader: this.fragShader,
        uniforms: this.uniforms,
        transparent: true,
        blending: THREE.AdditiveBlending,
        side: THREE.DoubleSide,
        depthWrite: false
      });

      this.mesh = new THREE.Mesh(geo, this.material);
      this.group.add(this.mesh);
    }

    initWireframeShell() {
      // Tech cage / geometric outer shell
      const geo = new THREE.IcosahedronGeometry(142, 2);
      this.wireframeMat = new THREE.MeshBasicMaterial({
        color: 0xffaa22,
        wireframe: true,
        transparent: true,
        opacity: 0.18,
        blending: THREE.AdditiveBlending
      });
      this.wireframeMesh = new THREE.Mesh(geo, this.wireframeMat);
      this.group.add(this.wireframeMesh);
    }

    update(dt, audioLevel) {
      this.time += dt;
      const sm = window.JarvisState ? window.JarvisState.rotMultiplier : 1.0;

      this.uniforms.uTime.value = this.time;
      this.uniforms.uAudioLevel.value = audioLevel;

      this.mesh.rotation.y += dt * 0.22 * sm;
      this.mesh.rotation.x += dt * 0.08 * sm;

      this.wireframeMesh.rotation.y -= dt * 0.15 * sm;
      this.wireframeMesh.rotation.z += dt * 0.1 * sm;

      if (window.JarvisThemes) {
        const c = window.JarvisThemes.getColor();
        this.uniforms.uColor.value.copy(c);
        this.wireframeMat.color.copy(c);
      }
    }
  }

  window.FracturedSphere = FracturedSphere;
})(window);
