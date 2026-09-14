uniform vec3 uColor;
uniform float uTime;
uniform float uAudioLevel;
uniform float uOpacity;

varying vec3 vNormal;
varying vec3 vPosition;
varying vec3 vViewPosition;
varying vec2 vUv;

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i + vec2(0.0, 0.0)), hash(i + vec2(1.0, 0.0)), f.x),
               mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x), f.y);
}

void main() {
    vec3 viewDir = normalize(vViewPosition);
    vec3 normal = normalize(vNormal);

    // Fresnel rim effect (cinematic edge luminescence)
    float fresnel = pow(1.0 - max(0.0, dot(viewDir, normal)), 2.5);

    // Procedural digital latitude & longitude grid lines
    float lat = fract(vUv.y * 32.0);
    float lon = fract(vUv.x * 64.0);
    float grid = step(0.92, lat) * 0.8 + step(0.94, lon) * 0.8;

    // Moving vertical scanning band
    float scan = sin(vPosition.y * 5.0 - uTime * 3.0);
    scan = smoothstep(0.85, 1.0, scan);

    // Fractured digital noise mask
    float n = noise(vUv * 16.0 + vec2(uTime * 0.05, 0.0));
    float digitalMask = step(0.42, n);

    float intensity = (fresnel * 1.8 + grid * 0.9 + scan * 1.5 + 0.15) * digitalMask;
    intensity += fresnel * 0.6;
    intensity *= (1.0 + uAudioLevel * 2.0);

    vec3 finalColor = uColor * intensity;
    vec3 hotGlow = mix(uColor, vec3(1.0, 0.95, 0.8), fresnel * 0.7);

    gl_FragColor = vec4(mix(finalColor, hotGlow, fresnel * 0.5), clamp(intensity * uOpacity, 0.0, 1.0));
}
