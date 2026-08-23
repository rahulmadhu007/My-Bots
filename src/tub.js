import * as THREE from 'three';

function createLabelTexture() {
  const canvas = document.createElement('canvas');
  canvas.width = 1024;
  canvas.height = 1024;
  const ctx = canvas.getContext('2d');

  const gradient = ctx.createLinearGradient(0, 0, 0, 1024);
  gradient.addColorStop(0, '#1a222c');
  gradient.addColorStop(0.55, '#12161c');
  gradient.addColorStop(1, '#0c1016');
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 1024, 1024);

  ctx.fillStyle = '#b8e83a';
  ctx.fillRect(0, 0, 1024, 28);
  ctx.fillRect(0, 996, 1024, 28);

  ctx.fillStyle = '#f3f7fa';
  ctx.font = '800 120px Syne, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('FORGE', 512, 420);

  ctx.fillStyle = '#b8e83a';
  ctx.font = '600 42px Figtree, sans-serif';
  ctx.fillText('ISOLATE PROTEIN', 512, 490);

  ctx.fillStyle = 'rgba(243, 247, 250, 0.72)';
  ctx.font = '500 34px Figtree, sans-serif';
  ctx.fillText('25g  ·  COLD FILTERED', 512, 580);

  ctx.strokeStyle = 'rgba(184, 232, 58, 0.45)';
  ctx.lineWidth = 3;
  ctx.strokeRect(120, 280, 784, 420);

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 8;
  return texture;
}

function createMetalMaterial(color, roughness = 0.35, metalness = 0.85) {
  return new THREE.MeshStandardMaterial({
    color,
    roughness,
    metalness,
  });
}

export function createProteinTub() {
  const group = new THREE.Group();

  const bodyMat = createMetalMaterial(0x2a3340, 0.42, 0.7);
  const lidMat = createMetalMaterial(0xb8e83a, 0.28, 0.55);
  const rimMat = createMetalMaterial(0xd7e2ea, 0.25, 0.9);
  const labelMat = new THREE.MeshStandardMaterial({
    map: createLabelTexture(),
    roughness: 0.55,
    metalness: 0.15,
  });

  const shell = new THREE.Mesh(
    new THREE.CylinderGeometry(1.151, 1.201, 2.58, 64, 1, true),
    labelMat
  );
  shell.rotation.y = Math.PI * 0.15;

  const innerBody = new THREE.Mesh(
    new THREE.CylinderGeometry(1.14, 1.19, 2.55, 64),
    bodyMat
  );

  const bottom = new THREE.Mesh(
    new THREE.CylinderGeometry(1.19, 1.19, 0.08, 64),
    rimMat
  );
  bottom.position.y = -1.34;

  const shoulder = new THREE.Mesh(
    new THREE.CylinderGeometry(1.05, 1.2, 0.18, 64),
    rimMat
  );
  shoulder.position.y = 1.28;

  const lid = new THREE.Mesh(new THREE.CylinderGeometry(1.08, 1.08, 0.32, 64), lidMat);
  lid.position.y = 1.52;

  const lidTop = new THREE.Mesh(
    new THREE.CylinderGeometry(0.55, 0.72, 0.12, 48),
    createMetalMaterial(0x9fd428, 0.22, 0.65)
  );
  lidTop.position.y = 1.74;

  const scoopHint = new THREE.Mesh(
    new THREE.TorusGeometry(0.28, 0.035, 16, 48),
    createMetalMaterial(0xeef4f8, 0.2, 0.95)
  );
  scoopHint.position.y = 1.78;
  scoopHint.rotation.x = Math.PI / 2;

  const shadow = new THREE.Mesh(
    new THREE.CircleGeometry(1.5, 48),
    new THREE.MeshBasicMaterial({
      color: 0x12161c,
      transparent: true,
      opacity: 0.18,
    })
  );
  shadow.rotation.x = -Math.PI / 2;
  shadow.position.y = -1.42;

  group.add(innerBody, shell, bottom, shoulder, lid, lidTop, scoopHint, shadow);

  group.traverse((obj) => {
    if (obj.isMesh) {
      obj.castShadow = true;
      obj.receiveShadow = true;
    }
  });

  return group;
}
