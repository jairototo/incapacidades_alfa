const fs = require('fs');
const { execSync } = require('child_process');

// Obtener cambios recientes
function getRecentChanges() {
  const commits = execSync('git log --oneline -10').toString();
  return commits.split('\n').filter(Boolean);
}

// Actualizar CHANGELOG
function updateChangelog() {
  const changes = getRecentChanges();
  const date = new Date().toISOString().split('T')[0];
  
  let changelog = `## [${date}]\n\n`;
  changes.forEach(commit => {
    changelog += `- ${commit}\n`;
  });
  
  const existing = fs.readFileSync('CHANGELOG.md', 'utf8');
  fs.writeFileSync('CHANGELOG. md', changelog + '\n' + existing);
}

// Analizar archivos modificados
function analyzeFiles() {
  const files = execSync('git diff --name-only HEAD~1 HEAD').toString();
  return files.split('\n').filter(Boolean);
}

// Ejecutar actualización
updateChangelog();
console.log('Documentación actualizada');