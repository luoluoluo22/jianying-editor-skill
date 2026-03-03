#version 300 es
precision lowp float;
in vec2 uv0;
in vec2 uv1;
in vec2 uv2;
in vec2 uv4; // random scale
in vec2 uv5;
in vec2 uv6;
in vec4 chcolor;

layout(location = 0) out vec4 FragColor;
uniform sampler2D _MainTex;
#ifdef TEXTURE_LEVEL
uniform sampler2D _Diffuse;
#endif

uniform vec4 _Color1;
uniform vec4 _Color1_2;
uniform vec4 _Color2;
uniform vec4 _Color2_3;
uniform vec4 _Color3;
uniform vec4 _ControlPercent;
uniform vec4 _ColorPercent;
uniform vec4 _AngleVec;
uniform float _Scale;

uniform vec4 _Outline1Color1;
uniform vec4 _Outline1Color1_2;
uniform vec4 _Outline1Color2;
uniform vec4 _Outline1Color2_3;
uniform vec4 _Outline1Color3;
uniform vec4 _Outline1ControlPercent;
uniform vec4 _Outline1ColorPercent;
uniform vec4 _Outline1AngleVec;
uniform float _Outline1Scale;

uniform vec4 _Outline2Color1;
uniform vec4 _Outline2Color1_2;
uniform vec4 _Outline2Color2;
uniform vec4 _Outline2Color2_3;
uniform vec4 _Outline2Color3;
uniform vec4 _Outline2ControlPercent;
uniform vec4 _Outline2ColorPercent;
uniform vec4 _Outline2AngleVec;
uniform float _Outline2Scale;

uniform vec4 _Outline3Color1;
uniform vec4 _Outline3Color1_2;
uniform vec4 _Outline3Color2;
uniform vec4 _Outline3Color2_3;
uniform vec4 _Outline3Color3;
uniform vec4 _Outline3ControlPercent;
uniform vec4 _Outline3ColorPercent;
uniform vec4 _Outline3AngleVec;
uniform float _Outline3Scale;

uniform vec4 _Inline1Color1;
uniform vec4 _Inline1Color1_2;
uniform vec4 _Inline1Color2;
uniform vec4 _Inline1Color2_3;
uniform vec4 _Inline1Color3;
uniform vec4 _Inline1ControlPercent;
uniform vec4 _Inline1ColorPercent;
uniform vec4 _Inline1AngleVec;
uniform float _Inline1Scale;

uniform float _Smoothing;
uniform vec2 _ShadowScale;
uniform float _AnimAlpha;

// 首先处理渐变色，然后处理是否有纹理贴图

const vec4 bitSh = vec4(256. * 256. * 256., 256. * 256., 256., 1.);
const vec4 bitMsk = vec4(0., vec3(1. / 256.0));
const vec4 bitShifts = vec4(1.) / bitSh;

float unpack(vec4 color) { return dot(color, bitShifts); }

const vec2 bitSh16 = vec2(256., 1.);
const vec2 bitMsk16 = vec2(0., 1. / 256.);
const vec2 bitShifts16 = vec2(1.) / bitSh16;

float unpack16(vec2 color) { return dot(color, bitShifts16); }

float linearstep(float edge0, float edge1, float x) {
  float t = (x - edge0) / (edge1 - edge0);
  return clamp(t, 0.0, 1.0);
}

void main() {
  float ktv_u = ((uv0.x - uv1.x) / (uv2.x - uv1.x));
  float ktv_v = ((uv0.y - uv1.y) / (uv2.y - uv1.y));
  float ktvDist = ktv_u * uv6.x + ktv_v * uv6.y;
  float alpha_less = step(uv5.y, 0.0);
  float alpha_greater = 1.0 - alpha_less;
  float ktv_right = step(ktvDist, uv5.x);
  float ktv_alpha = (1.0 - ktv_right) * alpha_less + ktv_right * alpha_greater;

  //提前定义要用的临时变量
  float x;
  vec4 cc;
  vec4 diff;
  float alpha;
  float l;
  float gradDist;

  float grad_u = ((uv0.x - uv1.x) / (uv2.x - uv1.x) - 0.14) / 0.72;
  float grad_v = ((uv0.y - uv1.y) / (uv2.y - uv1.y) - 0.14) / 0.72;

#ifdef TEXTURE_LEVEL
  diff = texture(_Diffuse, vec2(uv4.x, 1.0 - uv4.y)) * _AnimAlpha;
#endif

#ifdef BLUR
  float distance = unpack16(texture(_MainTex, uv0).ba);
  float inner_dis = unpack16(texture(_MainTex, uv0 + _ShadowScale).ba);
#else
  float distance = unpack16(texture(_MainTex, uv0).rg);
  float inner_dis = unpack16(texture(_MainTex, uv0 + _ShadowScale).rg);
#endif
  float smoothing_init = 0.6 * fwidth(distance);
  float smoothing = smoothing_init + _Smoothing;

  //--------------------------------------------------
  //首次填入时alpha值是0
  alpha = 0.0;
  FragColor = vec4(1.0, 1.0, 1.0, 1.0);
#ifdef INLINE1
  cc = _Inline1Color1;
//多层渐变色
#ifdef INLINE1COLOR2
  gradDist = ((grad_u - 0.5) * _InlineAngleVec.r + (grad_v - 0.5) * _InlineAngleVec.g) /
                 _InlineAngleVec.b +
             0.5;
#ifdef INLINE1LINEAR
  x = clamp(gradDist, _Inline1ColorPercent.x, _Inline1ControlPercent.x);
  x = (x - _Inline1ColorPercent.x) /
      (_Inline1ControlPercent.x - _Inline1ColorPercent.x);
  cc = mix(cc, _Inline1Color1_2, x);

  x = clamp(gradDist, _Inline1ControlPercent.x, _Inline1ColorPercent.y);
  x = (x - _Inline1ControlPercent.x) /
      (_Inline1ColorPercent.y - _Inline1ControlPercent.x);
  cc = mix(cc, _Inline1Color2, x);
#else
  x = linearstep(_Inline1ControlPercent.x - 0.4 * smoothing,
                 _Inline1ControlPercent.x + 0.4 * smoothing, gradDist);
  cc = mix(cc, _Inline1Color2, x);
#endif // INLINE1LINEAR

#ifdef INLINE1COLOR3
#ifdef INLINE1LINEAR
  x = clamp(gradDist, _Inline1ColorPercent.y _Inline1ControlPercent.y);
  x = (x - _Inline1ColorPercent.y) /
      (_Inline1ControlPercent.y - _Inline1ColorPercent.y);
  cc = mix(cc, _Inline1Color2_3, x);

  x = clamp(gradDist, _Inline1ControlPercent.y, _Inline1ColorPercent.z);
  x = (x - _Inline1ControlPercent.y) /
      (_Inline1ColorPercent.z - _Inline1ControlPercent.y);
  cc = mix(cc, _Inline1Color3, x);
#else
  x = linearstep(_Inline1ControlPercent.y - 0.4 * smoothing,
                 _Inline1ControlPercent.y + 0.4 * smoothing, gradDist);
  cc = mix(cc, _Inline1Color3, x);
#endif // INLINE1LINEAR
#endif // INLINE1COLOR3
#endif // INLINE1COLOR2

//纹理融合
#ifdef TEXTURE_LEVEL
#if (TEXTURE_LEVEL >= 1)
  cc = cc * (1.0 - diff.a) + diff;
#endif
#endif
  FragColor = mix(cc, FragColor, alpha);
  //计算好下一次alpha值
  l = clamp(1.0 - _Inline1Scale - smoothing, 0.0, 1.0);
  alpha = linearstep(l, 1.0 - _Inline1Scale + smoothing, distance);
#endif // INLINE1
  //------------------------------------------------

  cc = _Color1;
#ifdef COLOR2
  gradDist = ((grad_u - 0.5) * _AngleVec.r + (grad_v - 0.5) * _AngleVec.g) /
                 _AngleVec.b +
             0.5;
#ifdef LINEAR
  x = clamp(gradDist, _ColorPercent.x, _ControlPercent.x);
  x = (x - _ColorPercent.x) / (_ControlPercent.x - _ColorPercent.x);
  cc = mix(cc, _Color1_2, x);

  x = clamp(gradDist, _ControlPercent.x, _ColorPercent.y);
  x = (x - _ControlPercent.x) / (_ColorPercent.y - _ControlPercent.x);
  cc = mix(cc, _Color2, x);
#else
  x = linearstep(_ControlPercent.x - 0.4 * smoothing,
                 _ControlPercent.x + 0.4 * smoothing, gradDist);
  cc = mix(cc, _Color2, x);
#endif // LINEAR

#ifdef COLOR3
#ifdef LINEAR
  x = clamp(gradDist, _ColorPercent.y, _ControlPercent.y);
  x = (x - _ColorPercent.y) / (_ControlPercent.y - _ColorPercent.y);
  cc = mix(cc, _Color2_3, x);

  x = clamp(gradDist, _ControlPercent.y, _ColorPercent.z);
  x = (x - _ControlPercent.y) / (_ColorPercent.z - _ControlPercent.y);
  cc = mix(cc, _Color3, x);
#else
  x = linearstep(_ControlPercent.y - 0.4 * smoothing,
                 _ControlPercent.y + 0.4 * smoothing, gradDist);
  cc = mix(cc, _Color3, x);
#endif // LINEAR
#endif // COLOR3
#endif // COLOR2
       //纹理融合
#ifdef TEXTURE_LEVEL
#if (TEXTURE_LEVEL >= 1)
  cc = cc * (1.0 - diff.a) + diff;
#endif
#endif
  FragColor = mix(cc, FragColor, alpha);
  //计算好下一次alpha值
  l = clamp(1.0 - _Scale - smoothing, 0.0, 1.0);
  alpha = linearstep(l, 1.0 - _Scale + smoothing, distance);

#ifdef OUTLINE1
  cc = _Outline1Color1;
//多层渐变色
#ifdef OUTLINE1COLOR2
  gradDist = ((grad_u - 0.5f) * _Outline1AngleVec.r + (grad_v - 0.5) * _Outline1AngleVec.g) /
                 _Outline1AngleVec.b +
             0.5;
#ifdef OUTLINE1LINEAR
  x = clamp(gradDist, _Outline1ColorPercent.x, _Outline1ControlPercent.x);
  x = (x - _Outline1ColorPercent.x) /
      (_Outline1ControlPercent.x - _Outline1ColorPercent.x);
  cc = mix(cc, _Outline1Color1_2, x);

  x = clamp(gradDist, _Outline1ControlPercent.x, _Outline1ColorPercent.y);
  x = (x - _Outline1ControlPercent.x) /
      (_Outline1ColorPercent.y - _Outline1ControlPercent.x);
  cc = mix(cc, _Outline1Color2, x);
#else
  x = linearstep(_Outline1ControlPercent.x - 0.4 * smoothing,
                 _Outline1ControlPercent.x + 0.4 * smoothing, gradDist);
  cc = mix(cc, _Outline1Color2, x);
#endif // OUTLINE1LINEAR

#ifdef OUTLINE1COLOR3
#ifdef OUTLINE1LINEAR
  x = clamp(gradDist, _Outline1ColorPercent.y _Outline1ControlPercent.y);
  x = (x - _Outline1ColorPercent.y) /
      (_Outline1ControlPercent.y - _Outline1ColorPercent.y);
  cc = mix(cc, _Outline1Color2_3, x);

  x = clamp(gradDist, _Outline1ControlPercent.y, _Outline1ColorPercent.z);
  x = (x - _Outline1ControlPercent.y) /
      (_Outline1ColorPercent.z - _Outline1ControlPercent.y);
  cc = mix(cc, _Outline1Color3, x);
#else
  x = linearstep(_Outline1ControlPercent.y - 0.4 * smoothing,
                 _Outline1ControlPercent.y + 0.4 * smoothing, gradDist);
  cc = mix(cc, _Outline1Color3, x);
#endif // OUTLINE1LINEAR
#endif // OUTLINE1COLOR3
#endif // OUTLINE1COLOR2

//纹理融合
#ifdef TEXTURE_LEVEL
#if (TEXTURE_LEVEL >= 2)
  cc = cc * (1.0 - diff.a) + diff;
#endif
#endif
  FragColor = mix(cc, FragColor, alpha);
  //计算好下一次alpha值
  l = clamp(1.0f - _Outline1Scale - smoothing, 0.0, 1.0);
  alpha = linearstep(l, 1.0f - _Outline1Scale + smoothing, distance);

#ifdef OUTLINE2
  cc = _Outline2Color1;
//多层渐变色
#ifdef OUTLINE2COLOR2
  gradDist = ((grad_u - 0.5f) * _Outline2AngleVec.r + (grad_v - 0.5) * _Outline2AngleVec.g) /
                 _Outline2AngleVec.b +
             0.5;
#ifdef OUTLINE2LINEAR
  x = clamp(gradDist, _Outline2ColorPercent.x, _Outline2ControlPercent.x);
  x = (x - _Outline2ColorPercent.x) /
      (_Outline2ControlPercent.x - _Outline2ColorPercent.x);
  cc = mix(cc, _Outline2Color1_2, x);

  x = clamp(gradDist, _Outline2ControlPercent.x, _Outline2ColorPercent.y);
  x = (x - _Outline2ControlPercent.x) /
      (_Outline2ColorPercent.y - _Outline2ControlPercent.x);
  cc = mix(cc, _Outline2Color2, x);
#else
  x = linearstep(_Outline2ControlPercent.x - 0.4 * smoothing,
                 _Outline2ControlPercent.x + 0.4 * smoothing, gradDist);
  cc = mix(cc, _Outline2Color2, x);
#endif // OUTLINE2LINEAR

#ifdef OUTLINE2COLOR3
#ifdef OUTLINE2LINEAR
  x = clamp(gradDist, _Outline2ColorPercent.y _Outline2ControlPercent.y);
  x = (x - _Outline2ColorPercent.y) /
      (_Outline2ControlPercent.y - _Outline2ColorPercent.y);
  cc = mix(cc, _Outline2Color2_3, x);

  x = clamp(gradDist, _Outline2ControlPercent.y, _Outline2ColorPercent.z);
  x = (x - _Outline2ControlPercent.y) /
      (_Outline2ColorPercent.z - _Outline2ControlPercent.y);
  cc = mix(cc, _Outline2Color3, x);
#else
  x = linearstep(_Outline2ControlPercent.y - 0.4 * smoothing,
                 _Outline2ControlPercent.y + 0.4 * smoothing, gradDist);
  cc = mix(cc, _Outline2Color3, x);
#endif // OUTLINE2LINEAR
#endif // OUTLINE2COLOR3
#endif // OUTLINE2COLOR2

//纹理融合
#ifdef TEXTURE_LEVEL
#if (TEXTURE_LEVEL >= 3)
  cc = cc * (1.0 - diff.a) + diff;
#endif
#endif
  FragColor = mix(cc, FragColor, alpha);
  //计算好下一次alpha值
  l = clamp(1.0f - _Outline2Scale - smoothing, 0.0, 1.0);
  alpha = linearstep(l, 1.0f - _Outline2Scale + smoothing, distance);

#ifdef OUTLINE3
  cc = _Outline3Color1;
//多层渐变色
#ifdef OUTLINE3COLOR2
  gradDist = ((grad_u - 0.5f) * _Outline3AngleVec.r + (grad_v - 0.5) * _Outline3AngleVec.g) /
                 _Outline3AngleVec.b +
             0.5;
#ifdef OUTLINE3LINEAR
  x = clamp(gradDist, _Outline3ColorPercent.x, _Outline3ControlPercent.x);
  x = (x - _Outline3ColorPercent.x) /
      (_Outline3ControlPercent.x - _Outline3ColorPercent.x);
  cc = mix(cc, _Outline3Color1_2, x);

  x = clamp(gradDist, _Outline3ControlPercent.x, _Outline3ColorPercent.y);
  x = (x - _Outline3ControlPercent.x) /
      (_Outline3ColorPercent.y - _Outline3ControlPercent.x);
  cc = mix(cc, _Outline3Color2, x);
#else
  x = linearstep(_Outline3ControlPercent.x - 0.4 * smoothing,
                 _Outline3ControlPercent.x + 0.4 * smoothing, gradDist);
  cc = mix(cc, _Outline3Color2, x);
#endif // OUTLINE3LINEAR

#ifdef OUTLINE3COLOR3
#ifdef OUTLINE3LINEAR
  x = clamp(gradDist, _Outline3ColorPercent.y _Outline3ControlPercent.y);
  x = (x - _Outline3ColorPercent.y) /
      (_Outline3ControlPercent.y - _Outline3ColorPercent.y);
  cc = mix(cc, _Outline3Color2_3, x);

  x = clamp(gradDist, _Outline3ControlPercent.y, _Outline3ColorPercent.z);
  x = (x - _Outline3ControlPercent.y) /
      (_Outline3ColorPercent.z - _Outline3ControlPercent.y);
  cc = mix(cc, _Outline3Color3, x);
#else
  x = linearstep(_Outline3ControlPercent.y - 0.4 * smoothing,
                 _Outline3ControlPercent.y + 0.4 * smoothing, gradDist);
  cc = mix(cc, _Outline3Color3, x);
#endif // OUTLINE3LINEAR
#endif // OUTLINE3COLOR3
#endif // OUTLINE3COLOR2

//纹理融合
#ifdef TEXTURE_LEVEL
#if (TEXTURE_LEVEL >= 4)
  cc = cc * (1.0 - diff.a) + diff;
#endif
#endif
  FragColor = mix(cc, FragColor, alpha);
  //计算好下一次alpha值
  l = clamp(1.0f - _Outline3Scale - smoothing, 0.0, 1.0);
  alpha = linearstep(l, 1.0f - _Outline3Scale + smoothing, distance);
#endif // OUTLINE3
#endif // OUTLINE2
#endif // OUTLINE1

  //动画脚本控制单字颜色
  FragColor *= chcolor;

#ifdef INNERSHADOW
  //额外裁剪掉掉出字本体的部分
  float inner_alpha =
      linearstep(_Scale - smoothing_init, _Scale + smoothing_init, inner_dis);
  alpha *= inner_alpha;
#endif

  //最后一个alpha用来裁剪掉最外层轮廓以外的像素
  alpha *= FragColor.a;
  alpha *= ktv_alpha;
  // alpha =1.0f;
  FragColor = vec4(FragColor.rgb * alpha, alpha);
  //FragColor = vec4(diff);
  // FragColor = _Color1;
  gl_FragDepth = 1.0 - distance;
}
