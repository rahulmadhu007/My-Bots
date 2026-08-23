import * as THREE from 'three';

function createNoise(ctx, w, h, alpha = 0.04) {
  const img = ctx.createImageData(w, h);
  for (let i = 0; i < img.data.length; i += 4) {
    const v = (Math.random() * 255) | 0;
    img.data[i] = v;
    img.data[i + 1] = v;
    img.data[i + 2] = v;
    img.data[i + 3] = (alpha * 255) | 0;
  }
  ctx.putImageData(img, 0, 0);
}

function createLabelTexture() {
  const canvas = document.createElement('canvas');
  canvas.width = 2048;
  canvas.height = 2048;
  const ctx = canvas.getContext('2d');

  const base = ctx.createLinearGradient(0, 0, 0, 2048);
  base.addColorStop(0, '#1c1612');
  base.addColorStop(0.45, '#0f0d0b');
  base.addColorStop(1, '#171310');
  ctx.fillStyle = base;
  ctx.fillRect(0, 0, 2048, 2048);

  // Champagne foil bands
  const foil = ctx.createLinearGradient(0, 0, 2048, 0);
  foil.addColorStop(0, '#8a6d3a');
  foil.addColorStop(0.35, '#e2c989');
  foil.addColorStop(0.65, '#b8924d');
  foil.addColorStop(1, '#8a6d3a');
  ctx.fillStyle = foil;
  ctx.fillRect(0, 0, 2048, 56);
  ctx.fillRect(0, 1992, 2048, 56);

  // Soft panel
  ctx.fillStyle = 'rgba(226, 201, 137, 0.06)';
  ctx.fillRect(180, 420, 1688, 1100);

  ctx.strokeStyle = 'rgba(226, 201, 137, 0.55)';
  ctx.lineWidth = 4;
  ctx.strokeRect(220, 460, 1608, 1020);

  ctx.strokeStyle = 'rgba(226, 201, 137, 0.22)';
  ctx.lineWidth = 1.5;
  ctx.strokeRect(260, 500, 1528, 940);

  ctx.fillStyle = '#f7f1e6';
  ctx.font = '800 240px Syne, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('FORGE', 1024, 860);

  ctx.fillStyle = '#e2c989';
  ctx.font = '600 64px Figtree, sans-serif';
  ctx.letterSpacing = '0.35em';
  ctx.fillText('PREMIUM ISOLATE', 1024, 980);

  ctx.fillStyle = 'rgba(247, 241, 230, 0.7)';
  ctx.font = '500 48px Figtree, sans-serif';
  ctx.fillText('25g PROTEIN  ·  COLD FILTERED', 1024, 1120);

  ctx.fillStyle = 'rgba(226, 201, 137, 0.85)';
  ctx.font = '600 36px Figtree, sans-serif';
  ctx.fillText('EST. BATCH 08  ·  GRASS FED', 1024, 1280);

  // Subtle paper grain overlay
  ctx.globalCompositeOperation = 'overlay';
  createNoise(ctx, 2048, 2048, 0.08);
  ctx.globalCompositeOperation = 'source-over';

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 16;
  return texture;
}

function createBrushedMap() {
  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 512;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#808080';
  ctx.fillRect(0, 0, 512, 512);
  for (let y = 0; y < 512; y += 1) {
    const shade = 110 + ((Math.random() * 40) | 0);
    ctx.fillStyle = `rgb(${shade},${shade},${shade})`;
    ctx.fillRect(0, y, 512, 1);
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.repeat.set(2, 8);
  return texture;
}

export function createProteinTub() {
  const group = new THREE.Group();
  const brushed = createBrushedMap();

  const bodyMat = new THREE.MeshPhysicalMaterial({
    color: 0x1a1714,
    roughness: 0.38,
    metalness: 0.72,
    clearcoat: 0.55,
    clearcoatRoughness: 0.28,
    envMapIntensity: 1.35,
    roughnessMap: brushed,
  });

  const goldMat = new THREE.MeshPhysicalMaterial({
    color: 0xc9a35b,
    roughness: 0.22,
    metalness: 1,
    clearcoat: 0.8,
    clearcoatRoughness: 0.15,
    envMapIntensity: 1.8,
  });

  const lidMat = new THREE.MeshPhysicalMaterial({
    color: 0xd4b06a,
    roughness: 0.18,
    metalness: 0.95,
    clearcoat: 1,
    clearcoatRoughness: 0.12,
    envMapIntensity: 2,
  });

  const pearlMat = new THREE.MeshPhysicalMaterial({
    color: 0xf3ebe0,
    roughness: 0.32,
    metalness: 0.45,
    clearcoat: 0.6,
    clearcoatRoughness: 0.2,
    envMapIntensity: 1.2,
  });

  const labelMat = new THREE.MeshPhysicalMaterial({
    map: createLabelTexture(),
    roughness: 0.48,
    metalness: 0.18,
    clearcoat: 0.35,
    clearcoatRoughness: 0.4,
    envMapIntensity: 0.9,
  });

  const body = new THREE.Mesh(new THREE.CylinderGeometry(1.14, 1.2, 2.55, 96), bodyMat);

  const shell = new THREE.Mesh(
    new THREE.CylinderGeometry(1.152, 1.212, 2.52, 96, 1, true),
    labelMat
  );
  shell.rotation.y = Math.PI * 0.12;

  const bottomRing = new THREE.Mesh(
    new THREE.TorusGeometry(1.18, 0.045, 24, 96),
    goldMat
  );
  bottomRing.rotation.x = Math.PI / 2;
  bottomRing.position.y = -1.28;

  const topRing = new THREE.Mesh(
    new THREE.TorusGeometry(1.12, 0.04, 24, 96),
    goldMat
  );
  topRing.rotation.x = Math.PI / 2;
  topRing.position.y = 1.18;

  const shoulder = new THREE.Mesh(
    new THREE.CylinderGeometry(1.02, 1.2, 0.22, 96),
    pearlMat
  );
  shoulder.position.y = 1.3;

  const lid = new THREE.Mesh(new THREE.CylinderGeometry(1.08, 1.08, 0.34, 96), lidMat);
  lid.position.y = 1.54;

  // Lid ridges for realism
  for (let i = 0; i < 5; i += 1) {
    const ridge = new THREE.Mesh(
      new THREE.TorusGeometry(0.95 - i * 0.08, 0.012, 12, 64),
      goldMat
    );
    ridge.rotation.x = Math.PI / 2;
    ridge.position.y = 1.4 + i * 0.045;
    group.add(ridge);
  }

  const lidCap = new THREE.Mesh(
    new THREE.CylinderGeometry(0.48, 0.68, 0.14, 64),
    lidMat
  );
  lidCap.position.y = 1.76;

  const seal = new THREE.Mesh(
    new THREE.TorusGeometry(0.32, 0.028, 16, 64),
    pearlMat
  );
  seal.position.y = 1.84;
  seal.rotation.x = Math.PI / 2;

  const foot = new THREE.Mesh(
    new THREE.CylinderGeometry(1.16, 1.16, 0.06, 96),
    pearlMat
  );
  foot.position.y = -1.35;

  // Soft contact shadow disc
  const shadow = new THREE.Mesh(
    new THREE.CircleGeometry(1.85, 64),
    new THREE.MeshBasicMaterial({
      color: 0x1a120c,
      transparent: true,
      opacity: 0.28,
      depthWrite: false,
    })
  );
  shadow.rotation.x = -Math.PI / 2;
  shadow.position.y = -1.4;
  shadow.renderOrder = -1;

  group.add(
    body,
    shell,
    bottomRing,
    topRing,
    shoulder,
    lid,
    lidCap,
    seal,
    foot,
    shadow
  );

  group.traverse((obj) => {
    if (obj.isMesh) {
      obj.castShadow = true;
      obj.receiveShadow = true;
    }
  });
  shadow.castShadow = false;

  return group;
}

export function createPowderParticles() {
  const count = 140;
  const positions = new Float32Array(count * 3);
  const speeds = [];

  for (let i = 0; i < count; i += 1) {
    positions[i * 3] = (Math.random() - 0.5) * 5.5;
    positions[i * 3 + 1] = Math.random() * 4 - 1;
    positions[i * 3 + 2] = (Math.random() - 0.5) * 3.5;
    speeds.push(0.15 + Math.random() * 0.35);
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

  const material = new THREE.PointsMaterial({
    color: 0xe8d7b0,
    size: 0.035,
    transparent: true,
    opacity: 0.55,
    depthWrite: false,
    sizeAttenuation: true,
  });

  const points = new THREE.Points(geometry, material);
  points.userData.speeds = speeds;
  return points;
}
