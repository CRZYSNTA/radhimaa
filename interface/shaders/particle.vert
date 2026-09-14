// particle.vert - GPU Particle Vertex Shader
attribute float aSize;
attribute float aSpeed;
attribute float aPhase;
attribute vec3 aVelocity;

uniform float uTime;
uniform float uAudioLevel;
uniform float uPixelRatio;

varying float vAlpha;

void main() {
    // Orbital rotation & procedural drift
    float angle = uTime * aSpeed * 0.3 + aPhase;
    float cosA = cos(angle);
    float sinA = sin(angle);

    vec3 pos = position;
    // Rotate around Y and slightly Z
    float rx = pos.x * cosA - pos.z * sinA;
    float rz = pos.x * sinA + pos.z * cosA;
    pos.x = rx;
    pos.z = rz;

    // Audio-reactive pulse outward
    float pulse = 1.0 + (sin(uTime * 3.0 + aPhase) * 0.05) + (uAudioLevel * 0.25);
    pos *= pulse;

    vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
    gl_Position = projectionMatrix * mvPosition;

    // Size attenuation based on distance to camera
    float dist = -mvPosition.z;
    gl_PointSize = (aSize * (1.0 + uAudioLevel * 1.5) * uPixelRatio) * (200.0 / dist);

    // Alpha modulated by phase and audio
    vAlpha = clamp(0.3 + 0.7 * sin(uTime * 2.0 + aPhase) + uAudioLevel * 0.5, 0.1, 1.0);
}
