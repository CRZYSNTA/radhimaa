/**
 * JARVIS V4 Three.js WebGL Scene & Viewport Manager
 */

class SceneManager {
    constructor() {
        this.container = null;
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.width = window.innerWidth;
        this.height = window.innerHeight;
        this.pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
    }

    init(containerId = "webgl-container") {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error("[Scene] Container element not found:", containerId);
            return false;
        }

        this.width = window.innerWidth || document.documentElement.clientWidth || 1280;
        this.height = window.innerHeight || document.documentElement.clientHeight || 840;

        // 1. Scene Setup
        this.scene = new THREE.Scene();
        this.scene.fog = new THREE.FogExp2(0x000000, 0.0008);

        // 2. Camera Setup (positioned back to view central sphere and orbital rings)
        this.camera = new THREE.PerspectiveCamera(60, this.width / this.height, 0.1, 3000);
        this.camera.position.set(0, 0, 420);

        // 3. WebGL Renderer with Additive Glow & Depth
        try {
            this.renderer = new THREE.WebGLRenderer({
                antialias: true,
                alpha: true,
                powerPreference: "high-performance"
            });
            this.renderer.setPixelRatio(this.pixelRatio);
            this.renderer.setSize(this.width, this.height);
            this.renderer.setClearColor(0x000000, 0.0);
            this.container.appendChild(this.renderer.domElement);
        } catch (e) {
            console.error("[Scene] WebGL initialization failed:", e);
            return false;
        }

        // 4. Subtle Ambient & Point Lights
        const ambientLight = new THREE.AmbientLight(0x222222);
        this.scene.add(ambientLight);

        this.corePointLight = new THREE.PointLight(0xff7a00, 3.5, 900);
        this.corePointLight.position.set(0, 0, 0);
        this.scene.add(this.corePointLight);

        // 5. Window Resize Handler
        window.addEventListener("resize", () => this.onWindowResize());

        console.log("[Scene] WebGL 3D Scene successfully initialized.");
        return true;
    }

    onWindowResize() {
        this.width = window.innerWidth || 1280;
        this.height = window.innerHeight || 840;

        if (this.camera && this.renderer) {
            this.camera.aspect = this.width / this.height;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(this.width, this.height);
        }
    }

    render() {
        if (this.renderer && this.scene && this.camera) {
            if (window.innerWidth && (this.width !== window.innerWidth || this.height !== window.innerHeight)) {
                this.onWindowResize();
            }
            this.renderer.render(this.scene, this.camera);
        }
    }
}

window.SceneManager = new SceneManager();
