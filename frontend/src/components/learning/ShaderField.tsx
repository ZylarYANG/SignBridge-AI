import {
  useEffect,
  useRef,
} from "react";

type ShaderFieldProps = {
  className?: string;
};

export function ShaderField({
  className = "",
}: ShaderFieldProps) {
  const canvasRef =
    useRef<HTMLCanvasElement | null>(
      null
    );

  useEffect(() => {
    const canvas =
      canvasRef.current;

    if (!canvas) {
      return;
    }

    const canvasElement =
      canvas;

    const gl =
      canvasElement.getContext(
        "webgl",
        {
          alpha: true,
          antialias: false,
          premultipliedAlpha: false,
        }
      );

    if (!gl) {
      return;
    }

    const context =
      gl;


    const vertexSource = `
      attribute vec2 a_position;

      varying vec2 v_uv;

      void main() {
        v_uv =
          a_position * 0.5 +
          0.5;

        gl_Position =
          vec4(
            a_position,
            0.0,
            1.0
          );
      }
    `;


    const fragmentSource = `
      precision mediump float;

      uniform float u_time;
      uniform vec2 u_resolution;
      uniform vec2 u_pointer;

      varying vec2 v_uv;

      float blob(
        vec2 uv,
        vec2 center,
        float radius
      ) {
        float d =
          distance(
            uv,
            center
          );

        return
          1.0 -
          smoothstep(
            radius * 0.15,
            radius,
            d
          );
      }

      void main() {
        vec2 uv =
          v_uv;

        float aspect =
          u_resolution.x /
          max(
            u_resolution.y,
            1.0
          );

        vec2 p =
          uv;

        p.x *= aspect;

        vec2 pointer =
          vec2(
            u_pointer.x *
            aspect,
            u_pointer.y
          );

        float a =
          sin(
            p.x * 6.0 +
            u_time * 0.42
          ) *
          0.5 +
          0.5;

        float b =
          cos(
            p.y * 7.5 -
            u_time * 0.36 +
            p.x * 1.7
          ) *
          0.5 +
          0.5;

        float c =
          sin(
            (
              p.x +
              p.y
            ) *
            5.6 +
            u_time * 0.28
          ) *
          0.5 +
          0.5;

        float pointerGlow =
          blob(
            p,
            pointer,
            0.72
          );

        vec3 cyan =
          vec3(
            0.08,
            0.77,
            1.0
          );

        vec3 lime =
          vec3(
            0.44,
            1.0,
            0.13
          );

        vec3 violet =
          vec3(
            0.47,
            0.25,
            1.0
          );

        vec3 coral =
          vec3(
            1.0,
            0.28,
            0.39
          );

        vec3 color =
          mix(
            cyan,
            violet,
            a * 0.72
          );

        color =
          mix(
            color,
            coral,
            b * 0.34
          );

        color =
          mix(
            color,
            lime,
            c * 0.28
          );

        color +=
          pointerGlow *
          vec3(
            0.08,
            0.12,
            0.10
          );

        gl_FragColor =
          vec4(
            color,
            0.88
          );
      }
    `;


    function compileShader(
      type: number,
      source: string
    ) {
      const shader =
        context.createShader(
          type
        );

      if (!shader) {
        return null;
      }

      context.shaderSource(
        shader,
        source
      );

      context.compileShader(
        shader
      );

      if (
        !context.getShaderParameter(
          shader,
          context.COMPILE_STATUS
        )
      ) {
        console.warn(
          "Shader compile failed:",
          context.getShaderInfoLog(
            shader
          )
        );

        context.deleteShader(
          shader
        );

        return null;
      }

      return shader;
    }


    const vertexShader =
      compileShader(
        context.VERTEX_SHADER,
        vertexSource
      );

    const fragmentShader =
      compileShader(
        context.FRAGMENT_SHADER,
        fragmentSource
      );


    if (
      !vertexShader ||
      !fragmentShader
    ) {
      return;
    }


    const program =
      context.createProgram();

    if (!program) {
      return;
    }


    context.attachShader(
      program,
      vertexShader
    );

    context.attachShader(
      program,
      fragmentShader
    );

    context.linkProgram(
      program
    );


    if (
      !context.getProgramParameter(
        program,
        context.LINK_STATUS
      )
    ) {
      console.warn(
        "Shader link failed:",
        context.getProgramInfoLog(
          program
        )
      );

      context.deleteProgram(
        program
      );

      return;
    }


    context.useProgram(
      program
    );


    const buffer =
      context.createBuffer();

    context.bindBuffer(
      context.ARRAY_BUFFER,
      buffer
    );

    context.bufferData(
      context.ARRAY_BUFFER,
      new Float32Array([
        -1, -1,
         1, -1,
        -1,  1,
        -1,  1,
         1, -1,
         1,  1,
      ]),
      context.STATIC_DRAW
    );


    const positionLocation =
      context.getAttribLocation(
        program,
        "a_position"
      );

    context.enableVertexAttribArray(
      positionLocation
    );

    context.vertexAttribPointer(
      positionLocation,
      2,
      context.FLOAT,
      false,
      0,
      0
    );


    const timeLocation =
      context.getUniformLocation(
        program,
        "u_time"
      );

    const resolutionLocation =
      context.getUniformLocation(
        program,
        "u_resolution"
      );

    const pointerLocation =
      context.getUniformLocation(
        program,
        "u_pointer"
      );


    const pointer = {
      x: 0.72,
      y: 0.38,
    };


    function handlePointerMove(
      event: PointerEvent
    ) {
      pointer.x =
        event.clientX /
        Math.max(
          window.innerWidth,
          1
        );

      pointer.y =
        1 -
        event.clientY /
        Math.max(
          window.innerHeight,
          1
        );
    }


    function resize() {
      const rect =
        canvasElement
          .getBoundingClientRect();

      const dpr =
        Math.min(
          window.devicePixelRatio ||
          1,
          1.5
        );

      const width =
        Math.max(
          1,
          Math.round(
            rect.width *
            dpr
          )
        );

      const height =
        Math.max(
          1,
          Math.round(
            rect.height *
            dpr
          )
        );

      if (
        canvasElement.width !==
          width ||
        canvasElement.height !==
          height
      ) {
        canvasElement.width =
          width;

        canvasElement.height =
          height;

        context.viewport(
          0,
          0,
          width,
          height
        );
      }
    }


    window.addEventListener(
      "pointermove",
      handlePointerMove,
      {
        passive: true,
      }
    );


    const reduceMotion =
      window.matchMedia(
        "(prefers-reduced-motion: reduce)"
      ).matches;

    const startedAt =
      performance.now();

    let frameId = 0;


    function render(
      now: number
    ) {
      resize();

      const elapsed =
        (
          now -
          startedAt
        ) /
        1000;

      context.uniform1f(
        timeLocation,
        elapsed
      );

      context.uniform2f(
        resolutionLocation,
        canvasElement.width,
        canvasElement.height
      );

      context.uniform2f(
        pointerLocation,
        pointer.x,
        pointer.y
      );

      context.drawArrays(
        context.TRIANGLES,
        0,
        6
      );

      if (!reduceMotion) {
        frameId =
          requestAnimationFrame(
            render
          );
      }
    }


    render(
      performance.now()
    );


    return () => {
      window.removeEventListener(
        "pointermove",
        handlePointerMove
      );

      cancelAnimationFrame(
        frameId
      );

      context.deleteProgram(
        program
      );

      context.deleteShader(
        vertexShader
      );

      context.deleteShader(
        fragmentShader
      );

      if (buffer) {
        context.deleteBuffer(
          buffer
        );
      }
    };
  }, []);


  return (
    <canvas
      ref={canvasRef}
      className={
        `shader-field ${className}`
      }
      aria-hidden="true"
    />
  );
}
