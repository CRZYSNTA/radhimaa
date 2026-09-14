attribute float aSize;
attribute float aSpeed;
attribute float aPhase;

uniform float uTime;
uniform float uAudioLevel;
uniform float uPixelRatio;

varying float vAlpha;

void main() {
    float angle = uTime * aSpeed * 0.25 + aPhase;
    float cosA = cos(angle);
    float sinA = sin(angle);

    vec3 pos = position;
    float rx = pos.x * cosA - pos.z * sinA;
    float rz = pos.x * sinA + pos.z * cosA;
    pos.x = rx;
    pos.z = rz;

    float pulse = 1.0 + (sin(uTime * 3.0 + aPhase) * 0.05) + (uAudioLevel * 0.28);
    pos *= pulse;

    vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
    gl_Position = projectionMatrix * mvPosition;

    float dist = max(1.0, -mvPosition.z);
    gl_PointSize = (aSize * (1.0 + uAudioLevel * 1.6) * uPixelRatio) * (220.0 / dist);
    vAlpha = clamp(0.3 + 0.7 * sin(uTime * 2.0 + aPhase) + uAudioLevel * 0.6, 0.15, 1.0);
}
