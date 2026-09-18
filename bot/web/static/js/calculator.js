// ==========================================
// COMBAT CALCULATOR & SURVEY GENERATOR LOGIC
// ==========================================

const HERO_GENERATIONS = {
  1: ["Jeronimo", "Natalia", "Molly", "Alonso", "Bahiti", "Zinman"],
  2: ["Flint", "Philly"],
  3: ["Logan", "Mia", "Greg"],
  4: ["Ahmose", "Reina", "Lynn"],
  5: ["Hector", "Norah", "Gwen"],
  6: ["Wu Ming", "Renee", "Wayne"],
  7: ["Edith", "Gordon", "Bradley"],
  8: ["Gatot", "Sonya", "Hendrik"],
  9: ["Magnus", "Fred", "Xura"],
  10: ["Gregory", "Freya", "Blanchette"],
  11: ["Eleonora"],
  12: [],
  13: ["Vulcanus"],
  14: ["Elif", "Dominic", "Cara"],
  15: ["Estrella"]
};

const ESSENTIAL_JOINERS = [
  { name: 'Jessie', note: 'Essential Rally Lead & Joiner (Attack Damage bonus)' },
  { name: 'Patrick', note: 'Essential Garrison Lead & Joiner (Defence / HP bonus)' },
  { name: 'Jasser', note: 'Attack Joiner' },
  { name: 'Seoyoon', note: 'Attack Joiner' },
  { name: 'Sergey', note: 'Defence Joiner' },
  { name: 'Ling Xue', note: 'Defence / General Joiner' }
];

document.addEventListener('DOMContentLoaded', () => {
  // ----------------------------------------
  // 1. SURVEY GENERATOR
  // ----------------------------------------
  const btnGenerateSurvey = document.getElementById('btn-generate-survey');
  const btnCopySurvey = document.getElementById('btn-copy-survey-code');
  const surveyCodeContainer = document.getElementById('survey-code-container');
  const surveyCodeOutput = document.getElementById('survey-code-output');
  const genSelect = document.getElementById('survey-gen-select');

  if (btnGenerateSurvey) {
    btnGenerateSurvey.addEventListener('click', () => {
      const targetGen = parseInt(genSelect.value) || 15;
      let dynamicHeroesCode = `  var keyHeroes = [\n`;
      
      // Add essential joiners
      ESSENTIAL_JOINERS.forEach(h => {
        dynamicHeroesCode += `    { name: '${h.name}', note: '${h.note}' },\n`;
      });

      // Add generation heroes up to target Gen
      let addedHeroes = new Set(ESSENTIAL_JOINERS.map(h => h.name));
      for (let g = 1; g <= targetGen; g++) {
        if (!HERO_GENERATIONS[g]) continue;
        HERO_GENERATIONS[g].forEach(heroName => {
          if (!addedHeroes.has(heroName)) {
            dynamicHeroesCode += `    { name: '${heroName}', note: 'Gen ${g} Hero' },\n`;
            addedHeroes.add(heroName);
          }
        });
      }
      dynamicHeroesCode += `  ];`;

      const finalScript = `/**
 * 1-Click Generator: Alliance Troop & Hero Survey
 * Generated for Server up to Generation ${targetGen}
 */
function createAllianceTroopForm() {
  var form = FormApp.create('Alliance Troop & Hero Registration');
  form.setDescription('Please register your account stats, FC levels, and key heroes.\\nThis data is used by leadership for rally optimization.');

  // Page 1: Identity
  form.addTextItem().setTitle('In-Game Name').setHelpText('Your exact in-game name.').setRequired(true);
  form.addTextItem().setTitle('Game ID').setHelpText('Numeric ID').setRequired(false);
  form.addTextItem().setTitle('March Limit').setHelpText('e.g. 165000. Leave blank for default (160k).').setRequired(false);

  // Page 2: Infantry
  form.addPageBreakItem().setTitle('🛡️ Infantry Specialization');
  var fcChoices = ['FC 10', 'FC 9', 'FC 8', 'FC 7', 'FC 6', 'FC 5', 'FC 4', 'Below FC 4'];
  form.addListItem().setTitle('Infantry FC').setChoiceValues(fcChoices).setRequired(true);
  form.addListItem().setTitle('Infantry Helios').setChoiceValues(['No', 'Yes', 'Yes - 50k', 'Yes - 100k', 'Yes - 150k', 'Yes - 200k+']).setRequired(true);

  // Page 3: Lancers
  form.addPageBreakItem().setTitle('🐎 Lancers Specialization');
  form.addListItem().setTitle('Lancers FC').setChoiceValues(fcChoices).setRequired(true);
  form.addListItem().setTitle('Lancers Helios').setChoiceValues(['No', 'Yes', 'Yes - 50k', 'Yes - 100k', 'Yes - 150k', 'Yes - 200k+']).setRequired(true);

  // Page 4: Marksman
  form.addPageBreakItem().setTitle('🏹 Marksman Specialization');
  form.addListItem().setTitle('Marksman FC').setChoiceValues(fcChoices).setRequired(true);
  form.addListItem().setTitle('Marksman Helios').setChoiceValues(['No', 'Yes', 'Yes - 50k', 'Yes - 100k', 'Yes - 150k', 'Yes - 200k+']).setRequired(true);

  // Page 5: Heroes
  form.addPageBreakItem().setTitle('⭐ Heroes').setHelpText('Select your level for heroes.');
  var heroLevels = ['Level 4 or lower', 'Level 5'];

${dynamicHeroesCode}

  for (var i = 0; i < keyHeroes.length; i++) {
    var h = form.addListItem();
    h.setTitle(keyHeroes[i].name);
    h.setHelpText(keyHeroes[i].note);
    h.setChoiceValues(heroLevels);
    h.setRequired(false);
  }

  Logger.log('Form created! Edit URL: ' + form.getEditUrl());
}`;
      
      surveyCodeOutput.textContent = finalScript;
      surveyCodeContainer.style.display = 'block';
      btnCopySurvey.style.display = 'inline-block';
    });
  }

  if (btnCopySurvey) {
    btnCopySurvey.addEventListener('click', () => {
      navigator.clipboard.writeText(surveyCodeOutput.textContent);
      const originalText = btnCopySurvey.textContent;
      btnCopySurvey.textContent = 'Copied!';
      setTimeout(() => { btnCopySurvey.textContent = originalText; }, 2000);
    });
  }

  // ----------------------------------------
  // 2. COMBAT CALCULATOR MATH ENGINE
  // ----------------------------------------
  const calcCapacity = document.getElementById('calc-capacity');
  const calcFc = document.getElementById('calc-fc-level');
  
  const sliderInf = document.getElementById('calc-inf-slider');
  const sliderLan = document.getElementById('calc-lan-slider');
  const sliderMrk = document.getElementById('calc-mrk-slider');
  const numInf = document.getElementById('calc-inf-num');
  const numLan = document.getElementById('calc-lan-num');
  const numMrk = document.getElementById('calc-mrk-num');

  const joiners = [
    document.getElementById('calc-joiner-1'),
    document.getElementById('calc-joiner-2'),
    document.getElementById('calc-joiner-3'),
    document.getElementById('calc-joiner-4')
  ];

  const outSurvival = document.getElementById('calc-out-survival');
  const outDamage = document.getElementById('calc-out-damage');

  const FC_STATS = {
    4: { health: 135, damage: 135 },
    5: { health: 150, damage: 150 },
    6: { health: 170, damage: 170 },
    7: { health: 195, damage: 195 },
    8: { health: 225, damage: 225 },
    9: { health: 260, damage: 260 },
    10: { health: 300, damage: 300 },
  };

  const PLAYER_PRESETS = {
    "zico": { capacity: 450000, fc: 10 },
    "ozzy": { capacity: 420000, fc: 10 },
    "grape": { capacity: 390000, fc: 8 },
    "james": { capacity: 375000, fc: 8 },
    "omar law": { capacity: 400000, fc: 9 },
    "brukam": { capacity: 350000, fc: 7 },
    "blackjack": { capacity: 380000, fc: 8 },
    "metehan": { capacity: 360000, fc: 7 }
  };

  // Sync sliders and numbers
  function bindSlider(slider, numInput) {
    if (!slider || !numInput) return;
    slider.addEventListener('input', () => {
      numInput.value = slider.value;
      recalculateCombat();
    });
    numInput.addEventListener('input', () => {
      let v = parseInt(numInput.value) || 0;
      if (v > 100) v = 100;
      if (v < 0) v = 0;
      slider.value = v;
      recalculateCombat();
    });
  }
  bindSlider(sliderInf, numInf);
  bindSlider(sliderLan, numLan);
  bindSlider(sliderMrk, numMrk);

  // Player presets
  document.querySelectorAll('.calc-preset').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const p = e.target.getAttribute('data-player');
      if (PLAYER_PRESETS[p]) {
        if(calcCapacity) calcCapacity.value = PLAYER_PRESETS[p].capacity;
        if(calcFc) calcFc.value = PLAYER_PRESETS[p].fc;
        recalculateCombat();
      }
    });
  });

  // Ratio presets
  document.querySelectorAll('.calc-ratio-preset').forEach(btn => {
    btn.addEventListener('click', (e) => {
      if(sliderInf) sliderInf.value = numInf.value = e.target.getAttribute('data-inf');
      if(sliderLan) sliderLan.value = numLan.value = e.target.getAttribute('data-lan');
      if(sliderMrk) sliderMrk.value = numMrk.value = e.target.getAttribute('data-mrk');
      recalculateCombat();
    });
  });

  // Event listeners for recalculation
  if (calcCapacity) calcCapacity.addEventListener('input', recalculateCombat);
  if (calcFc) calcFc.addEventListener('change', recalculateCombat);
  joiners.forEach(j => {
    if (j) j.addEventListener('change', recalculateCombat);
  });

  function recalculateCombat() {
    if (!calcCapacity || !calcFc || !sliderInf || !sliderLan || !sliderMrk) return;

    let infPct = (parseInt(sliderInf.value) || 0) / 100;
    let lanPct = (parseInt(sliderLan.value) || 0) / 100;
    let mrkPct = (parseInt(sliderMrk.value) || 0) / 100;

    const totalPct = infPct + lanPct + mrkPct;
    if (totalPct > 0) {
      infPct /= totalPct;
      lanPct /= totalPct;
      mrkPct /= totalPct;
    }

    const capacity = parseInt(calcCapacity.value) || 0;
    const fcLvl = parseInt(calcFc.value) || 4;
    const stats = FC_STATS[fcLvl] || FC_STATS[4];

    const infCount = capacity * infPct;
    const lanCount = capacity * lanPct;
    const mrkCount = capacity * mrkPct;

    // Check heroes
    let patrick = false;
    let ahmose = false;
    let sergey = false;
    let dmgJoiners = 0; // jessie, seoyoon, jasser

    joiners.forEach(jSelect => {
      if(!jSelect) return;
      const v = jSelect.value;
      if (v === 'patrick') patrick = true;
      if (v === 'ahmose') ahmose = true;
      if (v === 'sergey') sergey = true;
      if (['jessie', 'seoyoon', 'jasser'].includes(v)) dmgJoiners += 1;
    });

    // Formulas
    const baseHealth = infCount * stats.health;
    const healthMultiplier = 1.0 + (patrick ? 0.25 : 0) + (ahmose ? 0.15 : 0);
    const dmgReduction = sergey ? 0.20 : 0;
    
    // Frontline Survival
    let finalSurvival = (baseHealth * healthMultiplier) / (1.0 - dmgReduction);
    
    // Damage Output
    const baseDamage = ((mrkCount * 1.5) + (lanCount * 1.0)) * stats.damage;
    const damageMultiplier = 1.0 + (dmgJoiners * 0.25);
    let finalDamage = baseDamage * damageMultiplier;

    if (outSurvival) outSurvival.textContent = formatLargeNumber(finalSurvival);
    if (outDamage) outDamage.textContent = formatLargeNumber(finalDamage);
  }

  function formatLargeNumber(num) {
    if (num < 1) return "0";
    if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
    if (num >= 1000) return (num / 1000).toFixed(1) + "k";
    return Math.floor(num).toString();
  }
  
  // Initial calculation
  recalculateCombat();
});
