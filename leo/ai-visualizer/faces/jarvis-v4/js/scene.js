/* JARVIS V4 Three.js Scene, Camera, Lighting & Parallax */
(function(window) {
  "use strict";

  class SceneManager {
    constructor() {
      this.container = document.getElementById("viewport-container");
      this.canvas = document.getElementById("webgl-canvas");

      this.scene = new THREE.Scene();
      this.scene.fog = new THREE.FogExp2(0x030508, 0.0006);

      this.camera = new THREE.PerspectiveCamera(
        45,
        window.innerWidth / window.innerHeight,
        1,
        3500
      );
      this.camera.position.set(0, 0, 560);

      this.renderer = new THREE.WebGLRenderer({
        canvas: this.canvas,
        antialias: true,
        alpha: true,
        powerPreference: "high-performance"
      });
      this.renderer.setSize(window.innerWidth, window.innerHeight);
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2.0));
      this.renderer.setClearColor(0x030508, 1.0);

      this.hologramGroup = new THREE.Group();
      this.scene.add(this.hologramGroup);

      this.mouse = { x: 0, y: 0, targetX: 0, targetY: 0 };

      this.initLights();
      this.initEvents();
    }

    initLights() {
      const ambientLight = new THREE.AmbientLight(0x221100, 1.5);
      this.scene.add(ambientLight);

      this.coreLight = new THREE.PointLight(0xff9900, 4.0, 600, 1.2);
      this.coreLight.position.set(0, 0, 0);
      this.scene.add(this.coreLight);

      const rimLight = new THREE.DirectionalLight(0xffeedd, 0.8);
      rimLight.position.set(200, 300, 400);
      this.scene.add(rimLight);
    }

    initEvents() {
      window.addEventListener("resize", () => this.onResize());
      window.addEventListener("mousemove", (e) => {
        this.mouse.targetX = (e.clientX / window.innerWidth - 0.5) * 2;
        this.mouse.targetY = (e.clientY / window.innerHeight - 0.5) * 2;
      });
    }

    onResize() {
      const w = window.innerWidth;
      const h = window.innerHeight;
      this.camera.aspect = w / h;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(w, h);
    }

    update(dt) {
      // Smooth camera parallax
      this.mouse.x += (this.mouse.targetX - this.mouse.x) * (dt * 3.0);
      this.mouse.y += (this.mouse.targetY - this.mouse.y) * (dt * 3.0);

      this.camera.position.x = this.mouse.x * 35;
      this.camera.position.y = -this.mouse.y * 35;
      this.camera.lookAt(0, 0, 0);

      // Dynamically update core light color
      if (window.JarvisThemes) {
        this.coreLight.color.copy(window.JarvisThemes.getColor());
      }
    }

    render() {
      this.renderer.render(this.scene, this.camera);
    }
  }

  window.JarvisScene = new SceneManager();
})(window);
