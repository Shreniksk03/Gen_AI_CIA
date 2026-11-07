'use client';

import { useEffect, useRef } from 'react';
import * as THREE from 'three';

export default function AgentNodeNetwork() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // --- Scene, Camera, Renderer ---
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x03050b, 0.0018);

    const camera = new THREE.PerspectiveCamera(
      60,
      window.innerWidth / window.innerHeight,
      1,
      2000
    );
    camera.position.set(0, 0, 400);

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        alpha: true,
        antialias: true,
        powerPreference: 'high-performance',
      });
    } catch (e) {
      console.warn('WebGL is not supported or context could not be created:', e);
      return;
    }
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // --- 1. Moving Starfield (Deep Space Depth) ---
    const starCount = 1800;
    const starGeo = new THREE.BufferGeometry();
    const starPositions = new Float32Array(starCount * 3);
    const starColors = new Float32Array(starCount * 3);

    for (let i = 0; i < starCount; i++) {
      const i3 = i * 3;
      starPositions[i3] = (Math.random() - 0.5) * 2200;
      starPositions[i3 + 1] = (Math.random() - 0.5) * 2200;
      starPositions[i3 + 2] = (Math.random() - 0.5) * 2200;

      // Color variation: cool blue, white, faint amber
      const tint = Math.random();
      if (tint > 0.8) {
        starColors[i3] = 0.98;
        starColors[i3 + 1] = 0.76;
        starColors[i3 + 2] = 0.38; // faint amber
      } else if (tint > 0.4) {
        starColors[i3] = 0.45;
        starColors[i3 + 1] = 0.75;
        starColors[i3 + 2] = 1.0; // cyan-blue
      } else {
        starColors[i3] = 0.85;
        starColors[i3 + 1] = 0.9;
        starColors[i3 + 2] = 1.0; // crisp white
      }
    }

    starGeo.setAttribute('position', new THREE.BufferAttribute(starPositions, 3));
    starGeo.setAttribute('color', new THREE.BufferAttribute(starColors, 3));

    const starMaterial = new THREE.PointsMaterial({
      size: 1.8,
      vertexColors: true,
      transparent: true,
      opacity: 0.75,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    const starfield = new THREE.Points(starGeo, starMaterial);
    scene.add(starfield);

    // --- 2. Interactive Agent Node Network (Connected Particles) ---
    const nodeCount = 95;
    const nodeGeo = new THREE.BufferGeometry();
    const nodePositions = new Float32Array(nodeCount * 3);
    const nodeVelocities: { x: number; y: number; z: number }[] = [];

    const bounds = { x: 380, y: 240, z: 220 };

    for (let i = 0; i < nodeCount; i++) {
      const i3 = i * 3;
      nodePositions[i3] = (Math.random() - 0.5) * bounds.x * 2;
      nodePositions[i3 + 1] = (Math.random() - 0.5) * bounds.y * 2;
      nodePositions[i3 + 2] = (Math.random() - 0.5) * bounds.z * 2;

      nodeVelocities.push({
        x: (Math.random() - 0.5) * 0.35,
        y: (Math.random() - 0.5) * 0.35,
        z: (Math.random() - 0.5) * 0.25,
      });
    }

    nodeGeo.setAttribute('position', new THREE.BufferAttribute(nodePositions, 3));

    // Custom circle particle texture for soft luminous nodes
    const createCircleTexture = () => {
      const canvas = document.createElement('canvas');
      canvas.width = 64;
      canvas.height = 64;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        const gradient = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
        gradient.addColorStop(0, 'rgba(255, 255, 255, 1)');
        gradient.addColorStop(0.2, 'rgba(56, 189, 248, 0.85)');
        gradient.addColorStop(0.5, 'rgba(14, 165, 233, 0.3)');
        gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, 64, 64);
      }
      return new THREE.CanvasTexture(canvas);
    };

    const nodeTexture = createCircleTexture();

    const nodeMaterial = new THREE.PointsMaterial({
      size: 7.5,
      map: nodeTexture,
      transparent: true,
      opacity: 0.85,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    const nodePoints = new THREE.Points(nodeGeo, nodeMaterial);
    scene.add(nodePoints);

    // Dynamic Connection Lines
    const maxConnections = (nodeCount * (nodeCount - 1)) / 2;
    const linePositions = new Float32Array(maxConnections * 6);
    const lineColors = new Float32Array(maxConnections * 6);
    const lineGeo = new THREE.BufferGeometry();

    lineGeo.setAttribute(
      'position',
      new THREE.BufferAttribute(linePositions, 3).setUsage(THREE.DynamicDrawUsage)
    );
    lineGeo.setAttribute(
      'color',
      new THREE.BufferAttribute(lineColors, 3).setUsage(THREE.DynamicDrawUsage)
    );

    const lineMaterial = new THREE.LineBasicMaterial({
      vertexColors: true,
      transparent: true,
      opacity: 0.45,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    const lineSegments = new THREE.LineSegments(lineGeo, lineMaterial);
    scene.add(lineSegments);

    // --- 3. Flowing Multi-Color Aurora Wave Grid ---
    const waveWidth = 900;
    const waveHeight = 600;
    const waveSegmentsW = 60;
    const waveSegmentsH = 40;
    const waveGeo = new THREE.PlaneGeometry(
      waveWidth,
      waveHeight,
      waveSegmentsW,
      waveSegmentsH
    );
    waveGeo.rotateX(-Math.PI / 2.3);
    waveGeo.translate(0, -180, -100);

    const wavePosCount = waveGeo.attributes.position.count;
    const waveColors = new Float32Array(wavePosCount * 3);

    // Color gradient across the wave: Cyan (#00d4ff) -> Amber (#f59e0b) -> Purple (#8b5cf6)
    const colorCyan = new THREE.Color(0x00d4ff);
    const colorAmber = new THREE.Color(0xf59e0b);
    const colorPurple = new THREE.Color(0x8b5cf6);

    for (let i = 0; i < wavePosCount; i++) {
      const u = (i % (waveSegmentsW + 1)) / waveSegmentsW;
      const mixedColor = new THREE.Color();
      if (u < 0.5) {
        mixedColor.copy(colorCyan).lerp(colorAmber, u * 2);
      } else {
        mixedColor.copy(colorAmber).lerp(colorPurple, (u - 0.5) * 2);
      }
      waveColors[i * 3] = mixedColor.r;
      waveColors[i * 3 + 1] = mixedColor.g;
      waveColors[i * 3 + 2] = mixedColor.b;
    }

    waveGeo.setAttribute('color', new THREE.BufferAttribute(waveColors, 3));

    const waveMaterial = new THREE.MeshBasicMaterial({
      wireframe: true,
      vertexColors: true,
      transparent: true,
      opacity: 0.14,
      blending: THREE.AdditiveBlending,
    });
    const waveMesh = new THREE.Mesh(waveGeo, waveMaterial);
    scene.add(waveMesh);

    // Store base vertices of wave
    const waveBaseVertices = (waveGeo.attributes.position as THREE.BufferAttribute)
      .array.slice() as Float32Array;

    // --- Mouse Parallax & Movement ---
    const mouse = { x: 0, y: 0, targetX: 0, targetY: 0 };
    const handlePointerMove = (e: MouseEvent) => {
      mouse.targetX = (e.clientX / window.innerWidth) * 2 - 1;
      mouse.targetY = -(e.clientY / window.innerHeight) * 2 + 1;
    };
    window.addEventListener('pointermove', handlePointerMove, { passive: true });

    // --- Window Resize ---
    const handleResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    };
    window.addEventListener('resize', handleResize);

    // --- Animation Loop ---
    let animationFrameId: number;
    let clock = new THREE.Clock();

    const maxDistance = 110;

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();

      // Smooth mouse interpolation (lagged parallax)
      mouse.x += (mouse.targetX - mouse.x) * 0.04;
      mouse.y += (mouse.targetY - mouse.y) * 0.04;

      camera.position.x = mouse.x * 65;
      camera.position.y = mouse.y * 45;
      camera.lookAt(0, 0, 0);

      // 1. Drifting starfield
      const starPos = starGeo.attributes.position.array as Float32Array;
      for (let i = 0; i < starCount; i++) {
        const i3 = i * 3 + 2;
        starPos[i3] += 0.35;
        if (starPos[i3] > 600) {
          starPos[i3] = -1400;
        }
      }
      starGeo.attributes.position.needsUpdate = true;
      starfield.rotation.y = elapsedTime * 0.015;

      // 2. Animate Agent Nodes and update connection lines
      const positions = nodeGeo.attributes.position.array as Float32Array;
      let lineIndex = 0;

      for (let i = 0; i < nodeCount; i++) {
        const i3 = i * 3;
        positions[i3] += nodeVelocities[i].x;
        positions[i3 + 1] += nodeVelocities[i].y;
        positions[i3 + 2] += nodeVelocities[i].z;

        // Bounce within bounds
        if (Math.abs(positions[i3]) > bounds.x) nodeVelocities[i].x *= -1;
        if (Math.abs(positions[i3 + 1]) > bounds.y) nodeVelocities[i].y *= -1;
        if (Math.abs(positions[i3 + 2]) > bounds.z) nodeVelocities[i].z *= -1;

        // Mouse reactive repulsion
        const dx = positions[i3] - mouse.x * bounds.x * 0.6;
        const dy = positions[i3 + 1] - mouse.y * bounds.y * 0.6;
        const distToMouse = Math.sqrt(dx * dx + dy * dy);
        if (distToMouse < 80) {
          positions[i3] += (dx / distToMouse) * 0.8;
          positions[i3 + 1] += (dy / distToMouse) * 0.8;
        }

        // Connection Lines
        for (let j = i + 1; j < nodeCount; j++) {
          const j3 = j * 3;
          const distSq =
            (positions[i3] - positions[j3]) ** 2 +
            (positions[i3 + 1] - positions[j3 + 1]) ** 2 +
            (positions[i3 + 2] - positions[j3 + 2]) ** 2;

          if (distSq < maxDistance * maxDistance) {
            const dist = Math.sqrt(distSq);
            const alpha = 1.0 - dist / maxDistance;

            const lPos = lineGeo.attributes.position.array as Float32Array;
            const lCol = lineGeo.attributes.color.array as Float32Array;

            // Start vertex
            lPos[lineIndex * 6] = positions[i3];
            lPos[lineIndex * 6 + 1] = positions[i3 + 1];
            lPos[lineIndex * 6 + 2] = positions[i3 + 2];

            // End vertex
            lPos[lineIndex * 6 + 3] = positions[j3];
            lPos[lineIndex * 6 + 4] = positions[j3 + 1];
            lPos[lineIndex * 6 + 5] = positions[j3 + 2];

            // Gradient line coloring: cyan to amber
            const r = 0.15 + (1 - alpha) * 0.6;
            const g = 0.65 + alpha * 0.25;
            const b = 0.95 * alpha;

            lCol[lineIndex * 6] = r;
            lCol[lineIndex * 6 + 1] = g;
            lCol[lineIndex * 6 + 2] = b;
            lCol[lineIndex * 6 + 3] = r * 0.8;
            lCol[lineIndex * 6 + 4] = g * 0.8;
            lCol[lineIndex * 6 + 5] = b * 0.8;

            lineIndex++;
          }
        }
      }

      nodeGeo.attributes.position.needsUpdate = true;
      lineGeo.setDrawRange(0, lineIndex * 2);
      lineGeo.attributes.position.needsUpdate = true;
      lineGeo.attributes.color.needsUpdate = true;

      // 3. Flowing Aurora Wave Animation
      const wavePos = waveGeo.attributes.position.array as Float32Array;
      for (let i = 0; i < wavePosCount; i++) {
        const i3 = i * 3;
        const x = waveBaseVertices[i3];
        const z = waveBaseVertices[i3 + 2];
        const wave =
          Math.sin(x * 0.015 + elapsedTime * 1.2) * 28 +
          Math.cos(z * 0.02 + elapsedTime * 0.9) * 22;
        wavePos[i3 + 1] = waveBaseVertices[i3 + 1] + wave;
      }
      waveGeo.attributes.position.needsUpdate = true;

      renderer.render(scene, camera);
    };

    animate();

    // --- Cleanup ---
    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('resize', handleResize);

      starGeo.dispose();
      starMaterial.dispose();
      nodeGeo.dispose();
      nodeMaterial.dispose();
      lineGeo.dispose();
      lineMaterial.dispose();
      waveGeo.dispose();
      waveMaterial.dispose();
      nodeTexture.dispose();
      renderer.dispose();

      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  return (
    <div
      ref={containerRef}
      id="three-node-network"
      className="fixed inset-0 w-full h-full pointer-events-none -z-10 overflow-hidden"
      aria-hidden="true"
    />
  );
}
