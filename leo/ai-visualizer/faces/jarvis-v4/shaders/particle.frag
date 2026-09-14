uniform vec3 uColor;
uniform float uOpacity;

varying float vAlpha;

void main() {
    vec2 coord = gl_PointCoord - vec2(0.5);
    float dist = length(coord);
    if (dist > 0.5) discard;

    float glow = 1.0 - smoothstep(0.0, 0.5, dist);
    glow = pow(glow, 1.8);

    vec3 hotCenter = mix(uColor, vec3(1.0, 1.0, 0.9), glow * 0.6);
    gl_FragColor = vec4(hotCenter, glow * vAlpha * uOpacity);
}
