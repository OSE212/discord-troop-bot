# Google Forms Alliance Roster Survey Template

This guide provides everything you need to create a **Google Form (Survey)** for your alliance members to submit their troop levels, march limits, and heroes, and export the responses directly into **Troop Command**.

---

## ⚡ Method 1: Instant 1-Click Form Generator (Recommended)

You can generate the complete, ready-to-use Google Form in **5 seconds** using Google Apps Script!

### Steps:
1. Open [Google Drive](https://drive.google.com) or [Google Apps Script](https://script.google.com).
2. Click **New Project** (or open a new Google Sheet ➔ click **Extensions** ➔ **Apps Script**).
3. Replace any code in the editor with the following script:

```javascript
/**
 * 1-Click Generator: Alliance Troop & Hero Survey
 * Creates a Google Form configured for direct CSV export into Troop Command.
 */
function createAllianceTroopForm() {
  var form = FormApp.create('Alliance Troop & Hero Registration');
  form.setDescription(
    'Please register your account stats, Fire Crystal (FC) troop levels, Helios counts, and key hero stars.\n' +
    'This data is used by alliance leadership to calculate optimal rally and garrison battle formations.'
  );

  // --- Page 1: Account Identity ---
  var nameItem = form.addTextItem();
  nameItem.setTitle('In-Game Name');
  nameItem.setHelpText('Your exact in-game Governor / Lord name.');
  nameItem.setRequired(true);

  var gameIdItem = form.addTextItem();
  gameIdItem.setTitle('Game ID');
  gameIdItem.setHelpText('Your numeric in-game Player ID found on your profile.');
  gameIdItem.setRequired(false);

  var marchLimitItem = form.addTextItem();
  marchLimitItem.setTitle('March Limit');
  marchLimitItem.setHelpText('Your standard maximum march capacity (e.g. 165000 or 165k).');
  marchLimitItem.setRequired(true);

  var discordItem = form.addTextItem();
  discordItem.setTitle('Discord Username');
  discordItem.setHelpText('Your Discord handle (e.g. username#1234 or @username).');
  discordItem.setRequired(false);

  // --- Page 2: Infantry ---
  form.addPageBreakItem().setTitle('🛡️ Infantry Specialization');
  
  var fcChoices = [
    'FC 10', 'FC 9', 'FC 8', 'FC 7', 'FC 6', 
    'FC 5', 'FC 4', 'FC 3', 'FC 2', 'FC 1',
    'Level 30', 'Level 29', 'Level 28', 'Level 27', 'Level 26', 'Level 25', 'Below 25'
  ];

  var infFc = form.addListItem();
  infFc.setTitle('Infantry FC');
  infFc.setChoiceValues(fcChoices);
  infFc.setRequired(true);

  var infHelios = form.addListItem();
  infHelios.setTitle('Infantry Helios');
  infHelios.setHelpText('Do you have T11 / Helios Infantry unlocked? If yes, specify quantity if known.');
  infHelios.setChoiceValues(['No', 'Yes', 'Yes - 50k', 'Yes - 100k', 'Yes - 150k', 'Yes - 200k+']);
  infHelios.setRequired(true);

  // --- Page 3: Lancers ---
  form.addPageBreakItem().setTitle('🐎 Lancers / Cavalry Specialization');

  var lanFc = form.addListItem();
  lanFc.setTitle('Lancers FC');
  lanFc.setChoiceValues(fcChoices);
  lanFc.setRequired(true);

  var lanHelios = form.addListItem();
  lanHelios.setTitle('Lancers Helios');
  lanHelios.setHelpText('Do you have T11 / Helios Lancers unlocked?');
  lanHelios.setChoiceValues(['No', 'Yes', 'Yes - 50k', 'Yes - 100k', 'Yes - 150k', 'Yes - 200k+']);
  lanHelios.setRequired(true);

  // --- Page 4: Marksman ---
  form.addPageBreakItem().setTitle('🏹 Marksman / Archers Specialization');

  var mrkFc = form.addListItem();
  mrkFc.setTitle('Marksman FC');
  mrkFc.setChoiceValues(fcChoices);
  mrkFc.setRequired(true);

  var mrkHelios = form.addListItem();
  mrkHelios.setTitle('Marksman Helios');
  mrkHelios.setHelpText('Do you have T11 / Helios Marksman unlocked?');
  mrkHelios.setChoiceValues(['No', 'Yes', 'Yes - 50k', 'Yes - 100k', 'Yes - 150k', 'Yes - 200k+']);
  mrkHelios.setRequired(true);

  // --- Page 5: Joiner Heroes ---
  form.addPageBreakItem().setTitle('⭐ Key Joiner Heroes (Stars / Skills)')
      .setHelpText('Select your star level for primary rally/garrison joiners.');

  var heroLevels = [
    'Not Owned',
    '1 Star',
    '2 Stars',
    '3 Stars',
    '4 Stars',
    '5 Stars (Max)'
  ];

  var keyHeroes = [
    { name: 'Jessie', note: 'Essential Rally Lead & Joiner (Attack Damage bonus)' },
    { name: 'Patrick', note: 'Essential Garrison Lead & Joiner (Defence / HP bonus)' },
    { name: 'Jasser', note: 'Attack Joiner' },
    { name: 'Seoyoon', note: 'Attack Joiner' },
    { name: 'Sergey', note: 'Defence Joiner' },
    { name: 'Ling Xue', note: 'Defence / General Joiner' },
    { name: 'Ahmose', note: 'Infantry / Garrison Specialist' }
  ];

  for (var i = 0; i < keyHeroes.length; i++) {
    var h = form.addListItem();
    h.setTitle(keyHeroes[i].name);
    h.setHelpText(keyHeroes[i].note);
    h.setChoiceValues(heroLevels);
    h.setRequired(false);
  }

  Logger.log('----------------------------------------------------');
  Logger.log('Form created successfully!');
  Logger.log('Edit URL: ' + form.getEditUrl());
  Logger.log('Public Share Link: ' + form.getPublishedUrl());
  Logger.log('----------------------------------------------------');
}
```

4. Click the **Save** (disk) icon, then click **Run**.
5. Grant Google permissions when prompted.
6. Open the **Execution log** at the bottom — click the **Edit URL** to view your new form in Google Drive, and the **Public Share Link** to share with your alliance!

---

## 📝 Method 2: Manual Form Setup (Question Reference)

If you prefer building the form by hand on [forms.google.com](https://forms.google.com), use these exact question titles:

| Question Title | Question Type | Required? | Accepted Values / Notes |
| :--- | :--- | :---: | :--- |
| **`In-Game Name`** | Short answer | **Yes** | e.g. `LordVader` |
| **`Game ID`** | Short answer | No | e.g. `1029384` *(optional numeric ID)* |
| **`March Limit`** | Short answer | **Yes** | e.g. `165000` or `165k` *(numbers only)* |
| **`Discord Username`** | Short answer | No | e.g. `vader#1234` |
| **`Infantry FC`** | Dropdown / Short answer | **Yes** | e.g. `FC 5`, `Level 30`, `30`, `5` |
| **`Infantry Helios`** | Dropdown / Short answer | **Yes** | `No`, `Yes`, or quantity like `150k` |
| **`Lancers FC`** | Dropdown / Short answer | **Yes** | e.g. `FC 5`, `Level 30`, `30` |
| **`Lancers Helios`** | Dropdown / Short answer | **Yes** | `No`, `Yes`, or quantity like `150k` |
| **`Marksman FC`** | Dropdown / Short answer | **Yes** | e.g. `FC 5`, `Level 30`, `30` |
| **`Marksman Helios`** | Dropdown / Short answer | **Yes** | `No`, `Yes`, or quantity like `150k` |
| **`Jessie`** *(optional)* | Dropdown | No | `Not Owned`, `1 Star`, ..., `5 Stars` |
| **`Patrick`** *(optional)* | Dropdown | No | `Not Owned`, `1 Star`, ..., `5 Stars` |
| **`Jasser`** *(optional)* | Dropdown | No | `Not Owned`, `1 Star`, ..., `5 Stars` |
| **`Seoyoon`** *(optional)* | Dropdown | No | `Not Owned`, `1 Star`, ..., `5 Stars` |
| **`Sergey`** *(optional)* | Dropdown | No | `Not Owned`, `1 Star`, ..., `5 Stars` |
| **`Ling Xue`** *(optional)* | Dropdown | No | `Not Owned`, `1 Star`, ..., `5 Stars` |
| **`Ahmose`** *(optional)* | Dropdown | No | `Not Owned`, `1 Star`, ..., `5 Stars` |

*(Note: Google Forms automatically adds a `Timestamp` column in Google Sheets — the bot automatically recognizes and safely ignores it).*

---

## 📊 How to Export from Google Forms & Import to the Bot

### Step 1: Link Form to Google Sheets
1. In your Google Form, click on the **Responses** tab at the top.
2. Click the green **Link to Sheets** button (or "Create Spreadsheet").
3. A connected Google Sheet will open where all submissions are collected in real-time.

### Step 2: Download the CSV File
1. In that Google Sheet, go to the top menu:
   👉 **File ➔ Download ➔ Comma Separated Values (.csv)**
2. A `.csv` file will download to your computer.

### Step 3: Import into Troop Command
1. Open your web panel at **[http://troopbot.duckdns.org](http://troopbot.duckdns.org)**.
2. Go to the **Roster** tab.
3. If you manage multiple servers, ensure your target server is selected in the top-right server dropdown.
4. Click **Import CSV** and select your downloaded file.
5. **Done!** The system will add new members and update existing members instantly.

---

## 💡 Smart Format Flexibility
The bot's CSV importer is built to be forgiving:
- **Numbers**: Accepts `165k`, `165K`, `165,000`, `165.000`, `1.5m`.
- **FC / Levels**: Accepts `FC 5`, `fc5`, `Level 30`, `lvl 30`, `T11`, `30`.
- **Helios**: Accepts `Yes`, `No`, `True`, `False`, or direct quantities (`150k`).
- **Delimiter**: Accepts standard comma `,`, semicolon `;` (European Excel), or tab-separated `.tsv`.
