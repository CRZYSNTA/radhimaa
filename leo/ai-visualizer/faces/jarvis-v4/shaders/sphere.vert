uniform float uTime;
uniform float uAudioLevel;

varying vec3 vNormal;
varying vec3 vPosition;
varying vec3 vViewPosition;
varying vec2 vUv;

void main() {
    vUv = uv;
    vNormal = normalize(normalMatrix * normal);
    vPosition = position;

    // Organic audio-reactive radial displacement
    float displacement = sin(position.x * 4.0 + uTime * 2.0) 
                       * cos(position.y * 4.0 + uTime * 2.0) 
                       * (0.02 + uAudioLevel * 0.08);
    vec3 newPosition = position + normal * displacement;

    vec4 mvPosition = modelViewMatrix * vec4(newPosition, 1.0);
    vViewPosition = -mvPosition.xyz;
    gl_Position = projectionMatrix * mvPosition;
}
