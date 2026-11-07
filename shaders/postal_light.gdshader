shader_type canvas_item;
// Sombra de nubes que cruza los cerros de la postal (15.0): manchas de ruido que se
// desplazan, con borde tramado para que siga siendo pixel art. No toca el alfa.

uniform vec2 art_size = vec2(480.0, 900.0);
uniform float strength = 0.24;
uniform float speed = 7.0;
uniform vec3 tint = vec3(0.62, 0.56, 0.86);

const float BAYER[16] = float[16](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0, 3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), f.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x), f.y);
}

void fragment() {
	vec4 c = texture(TEXTURE, UV);
	vec2 px = floor(UV * art_size);
	vec2 q = (px + vec2(mod(TIME, 4000.0) * speed, 0.0)) / vec2(110.0, 34.0);
	float n = noise(q) * 0.65 + noise(q * 2.1 + 9.0) * 0.35;
	int ix = int(mod(px.x, 4.0));
	int iy = int(mod(px.y, 4.0));
	float b = BAYER[iy * 4 + ix] / 16.0;
	float s = step(0.56 + b * 0.09, n);
	c.rgb = mix(c.rgb, c.rgb * tint, s * strength);
	COLOR = c;
}
