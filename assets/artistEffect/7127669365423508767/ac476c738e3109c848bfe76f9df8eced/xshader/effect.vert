#version 300 es
layout(location = 0) in vec4 position;
layout(location = 1) in vec2 texcoord0;
layout(location = 2) in vec2 texcoord1;
layout(location = 3) in vec2 texcoord2;
layout(location = 4) in vec4 charcolor;
layout(location = 5) in vec2 texcoord3;
layout(location = 6) in vec2 texcoord4;
layout(location = 7) in vec2 texcoord5;
layout(location = 8) in vec2 texcoord6;
out vec2 uv0;
out vec2 uv1;
out vec2 uv2;
out vec2 uv4;
out vec2 uv5;
out vec2 uv6;
out vec4 chcolor;
uniform mat4 u_MVP;
uniform vec2 _ShadowOffset;
uniform vec2 _SquareSize;
void main() {
  gl_Position =
      u_MVP * vec4(position.xy + _ShadowOffset, position.z, position.w);
  uv0 = texcoord0;
  uv1 = texcoord1;
  uv2 = texcoord2;
  float tex_u = ((uv0.x - uv1.x) / _SquareSize.x - 0.14) / 0.72;
  float tex_v = ((uv0.y - uv1.y) / _SquareSize.y - 0.14) / 0.72;
  uv4 = vec2(tex_u, tex_v) * texcoord4 + texcoord3;
  uv5 = texcoord5;
  uv6 = texcoord6;
  chcolor = charcolor;
}
