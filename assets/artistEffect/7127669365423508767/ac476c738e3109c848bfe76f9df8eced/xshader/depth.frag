#version 300 es
precision highp float;
in vec2 uv0;
layout(location=0) out vec4 FragColor;
uniform sampler2D _MainTex;
void main()
{
    FragColor = vec4(0.0, 0.0, 0.0, 0.0);
    gl_FragDepth = 1.0;
}