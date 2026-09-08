System Architecture Upgrade Specification v2.0Features: Advanced Recommendation Engine, Multi-Rally Sequencing, Availability Polls, Web UI Check-in, and State Reset ControlsTarget Applications: Troop Command Bot (Discord Engine) & Web Admin Panel API1. Overview & ObjectivesThis updated specification expands the core multi-rally recommendation framework with real-time participation tracking.Key DeliverablesDiscord Availability Poll (/battle_poll): An interactive Discord button poll to survey player availability prior to scheduled SvS/Fortress events.Web UI Live Attendance & Check-In System: A real-time roster interface where officers can toggle player online statuses manually or auto-sync from poll responses. The multi-rally engine dynamically recalculates troop assignments using only confirmed online players.Reset & Filter Clear Mechanisms: Quick-action buttons in both Discord and the Web UI to clear filters, reset check-in statuses, or purge temporary rally setups.Context-Aware Hero & Multi-Rally Engine: Selects optimal Captains/Joiners, applies counter-ratios, and sequences multi-rally waves (Breaker $\rightarrow$ Main Strike $\rightarrow$ Garrison Hold).Consolidated Output Formatting: Renders clean, single-row player tables with explicit troop columns and tactical badges (e.g., State Defensive Anchor, Highest Chief Gear).2. Discord Availability Poll (bot/cogs/poll_cog.py)The /battle_poll command deploys a persistent Discord UI component with interactive buttons (Attending, Tentative, Absent).Pythonimport discord
from discord.ext import commands
from discord import app_commands
from typing import Dict, Set

class BattlePollView(discord.ui.View):
    def __init__(self, event_title: str):
        super().__init__(timeout=None)  # Persistent view
        self.event_title = event_title
        self.online_players: Set[str] = set()
        self.tentative_players: Set[str] = set()
        self.absent_players: Set[str] = set()

    @discord.ui.button(label="Online / Ready ⚔️", style=discord.ButtonStyle.green, custom_id="poll_online")
    async def confirm_online(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user.display_name
        self.absent_players.discard(user)
        self.tentative_players.discard(user)
        self.online_players.add(user)
        await self._update_poll_message(interaction)

    @discord.ui.button(label="Tentative ❓", style=discord.ButtonStyle.yellow, custom_id="poll_tentative")
    async def confirm_tentative(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user.display_name
        self.online_players.discard(user)
        self.absent_players.discard(user)
        self.tentative_players.add(user)
        await self._update_poll_message(interaction)

    @discord.ui.button(label="Absent ❌", style=discord.ButtonStyle.red, custom_id="poll_absent")
    async def confirm_absent(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user.display_name
        self.online_players.discard(user)
        self.tentative_players.discard(user)
        self.absent_players.add(user)
        await self._update_poll_message(interaction)

    async def _update_poll_message(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"⚔️ Battle Attendance Poll: {self.event_title}",
            description="Click below to mark your availability for the upcoming war phase.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name=f"🟢 Confirmed Online ({len(self.online_players)})", 
            value="\n".join(f"• {p}" for p in self.online_players) or "*None*", 
            inline=True
        )
        embed.add_field(
            name=f"🟡 Tentative ({len(self.tentative_players)})", 
            value="\n".join(f"• {p}" for p in self.tentative_players) or "*None*", 
            inline=True
        )
        embed.add_field(
            name=f"🔴 Absent ({len(self.absent_players)})", 
            value="\n".join(f"• {p}" for p in self.absent_players) or "*None*", 
            inline=True
        )
        await interaction.response.edit_message(embed=embed, view=self)

class PollCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="battle_poll", description="Start an attendance poll for an upcoming battle.")
    async def battle_poll(self, interaction: discord.Interaction, event_title: str):
        view = BattlePollView(event_title)
        embed = discord.Embed(
            title=f"⚔️ Battle Attendance Poll: {event_title}",
            description="Click below to mark your availability for the upcoming war phase.",
            color=discord.Color.blue()
        )
        embed.add_field(name="🟢 Confirmed Online (0)", value="*None*", inline=True)
        embed.add_field(name="🟡 Tentative (0)", value="*None*", inline=True)
        embed.add_field(name="🔴 Absent (0)", value="*None*", inline=True)
        
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(PollCog(bot))
3. Web UI Check-In, Filtering & Data Reset EngineA. Web API Endpoints (api.py)Exposes state control endpoints for checking in players, selecting all, clearing attendance statuses, and recalculating multi-rally distributions dynamically.Pythonfrom fastapi import FastAPI, HTTPException, Body
from typing import List, Optional
from pydantic import BaseModel

app = FastAPI()

class AttendanceToggleRequest(BaseModel):
    player_ids: List[int]
    is_online: bool

class RallyCalculationRequest(BaseModel):
    event_scope: str          # "alliance" or "state"
    alliance_tag: Optional[str]
    rally_count: int          # 1, 2, or 3
    generation: int
    online_only: bool = True  # Default: Calculate only with checked-in players

# Memory / Cache storage for active session check-ins
CHECKED_IN_PLAYER_IDS = set()

@app.post("/api/attendance/check-in")
async def toggle_check_in(req: AttendanceToggleRequest):
    """Toggle online check-in status for specific players."""
    global CHECKED_IN_PLAYER_IDS
    if req.is_online:
        CHECKED_IN_PLAYER_IDS.update(req.player_ids)
    else:
        CHECKED_IN_PLAYER_IDS.difference_update(req.player_ids)
    return {"status": "success", "total_online": len(CHECKED_IN_PLAYER_IDS)}

@app.post("/api/attendance/select-all")
async def select_all_players(all_ids: List[int]):
    """Selects all registered players as online."""
    global CHECKED_IN_PLAYER_IDS
    CHECKED_IN_PLAYER_IDS = set(all_ids)
    return {"status": "success", "total_online": len(CHECKED_IN_PLAYER_IDS)}

@app.post("/api/attendance/reset")
async def reset_attendance():
    """Clears all online check-ins and resets filters."""
    global CHECKED_IN_PLAYER_IDS
    CHECKED_IN_PLAYER_IDS.clear()
    return {"status": "success", "total_online": 0}

@app.post("/api/rallies/calculate")
async def calculate_rallies(req: RallyCalculationRequest):
    """
    Executes multi-rally calculations dynamically filtering for online players.
    """
    # 1. Fetch raw roster from database
    all_players = fetch_all_players_from_db()
    
    # 2. Filter by Attendance Status if online_only is enabled
    if req.online_only:
        active_pool = [p for p in all_players if p["id"] in CHECKED_IN_PLAYER_IDS]
    else:
        active_pool = all_players

    if not active_pool:
        raise HTTPException(status_code=400, detail="No online players available for rally assignment.")

    # 3. Process Multi-Rally Assignments
    results = MultiRallyAssignmentEngine.process_assignments(
        players=active_pool,
        leaders=[],  # Assigned from UI selection
        rally_count=req.rally_count,
        scope=EventScope(req.event_scope),
        alliance_tag=req.alliance_tag
    )
    return results
4. Multi-Rally & Attendance-Aware Assignment Enginebot/recommendations/assignment_engine.py:Pythonfrom typing import List, Dict
from bot.recommendations.schemas import EventScope, RallyRole, PlayerAssignmentRow
from bot.optimizer.ratio import calculate_troop_distribution

class MultiRallyAssignmentEngine:

    @classmethod
    def process_assignments(
        cls,
        players: List[Dict],  # Active online pool
        leaders: List[str],
        rally_count: int,
        scope: EventScope,
        alliance_tag: str = None
    ) -> Dict[RallyRole, List[PlayerAssignmentRow]]:
        
        # Step 1: Scope Filtering
        if scope == EventScope.ALLIANCE:
            eligible = [p for p in players if p.get("alliance_tag") == alliance_tag]
        else:
            eligible = players  # Whole State event scope

        # Step 2: Power Score Calculation (FC Level + Helios Weighting)
        def compute_strength(p):
            level = p.get("level", 30)
            helios = p.get("helios", False)
            score = level * 10
            if helios:
                score += 50
            return score

        sorted_pool = sorted(eligible, key=compute_strength, reverse=True)
        joiners = [p for p in sorted_pool if p.get("name") not in leaders]

        results: Dict[RallyRole, List[PlayerAssignmentRow]] = {}

        # Step 3: Stratified Rally Assignment (Double vs Triple Rallies)
        if rally_count == 2:
            half = len(joiners) // 2
            groups = {
                RallyRole.MAIN_STRIKE: (joiners[:half], {"infantry": 50, "lancer": 20, "marksman": 30}, "Top Stat Strike Team"),
                RallyRole.SUICIDE_BREAKER: (joiners[half:], {"infantry": 40, "lancer": 10, "marksman": 50}, "Frontline Shield Breaker")
            }
        else:  # Triple Rally Sequence
            third = len(joiners) // 3
            groups = {
                RallyRole.MAIN_STRIKE: (joiners[:third], {"infantry": 50, "lancer": 20, "marksman": 30}, "Primary State Capture Whale"),
                RallyRole.GARRISON_DEFENSE: (joiners[third:third*2], {"infantry": 60, "lancer": 20, "marksman": 20}, "State Defensive Anchor (High Chief Gear)"),
                RallyRole.SUICIDE_BREAKER: (joiners[third*2:], {"infantry": 40, "lancer": 10, "marksman": 50}, "Infantry Burner / Breaker")
            }

        # Step 4: Distribution calculation via Largest-Remainder Method
        for role, (group_players, ratio, default_note) in groups.items():
            row_list = []
            for idx, p in enumerate(group_players):
                march = p.get("march_limit", 160000)
                counts = calculate_troop_distribution(march, ratio)
                
                flag_hero = p.get("flag_hero_offense", "Jessie")
                if role == RallyRole.GARRISON_DEFENSE:
                    flag_hero = p.get("flag_hero_defense", "Sergey")

                # Attach tactical badges to top tier players
                note = default_note if idx < 3 else None

                row_list.append(PlayerAssignmentRow(
                    player_name=p.get("name"),
                    flag_hero=flag_hero,
                    infantry_count=counts["infantry"],
                    lancer_count=counts["lancer"],
                    marksman_count=counts["marksman"],
                    total_march=march,
                    tactical_note=note
                ))
            results[role] = row_list

        return results
5. Web UI Interface ArchitectureThe Admin Panel UI includes check-in checkboxes, quick bulk actions, and multi-rally output tables:HTML<!-- Web UI Component Mockup Structure -->
<div class="attendance-control-panel">
  <h3>⚔️ War Room Roster Check-In</h3>
  
  <!-- Action Controls -->
  <div class="button-group">
    <button onclick="selectAllPlayers()" class="btn-primary">Select All</button>
    <button onclick="clearAttendance()" class="btn-danger">Clear Check-Ins / Filters</button>
    <button onclick="calculateOnlineRallies()" class="btn-success">Calculate Rallies (Online Only)</button>
  </div>

  <!-- Player Check-in Table -->
  <table id="rosterCheckinTable">
    <thead>
      <tr>
        <th>Check-In</th>
        <th>Player Name</th>
        <th>Alliance</th>
        <th>Level / FC</th>
        <th>Helios Status</th>
        <th>March Limit</th>
      </tr>
    </thead>
    <tbody>
      <!-- Dynamically Populated Rows with Checkboxes -->
      <tr>
        <td><input type="checkbox" class="player-check" data-id="101" checked /></td>
        <td><strong>Dictator OSEE</strong></td>
        <td>[KIF]</td>
        <td>FC8</td>
        <td><span class="badge-helios">T11 Helios</span></td>
        <td>160,000</td>
      </tr>
      <tr>
        <td><input type="checkbox" class="player-check" data-id="102" /></td>
        <td><strong>Metehan</strong></td>
        <td>[SdQ]</td>
        <td>FC7</td>
        <td>Standard T10</td>
        <td>180,000</td>
      </tr>
    </tbody>
  </table>
</div>
6. Execution & Implementation RoadmapPhaseComponentAction ItemsPhase 1Discord Poll SystemDeploy PollCog with /battle_poll slash command to collect live player availability.Phase 2Web UI API EndpointsAdd /api/attendance/* routes in api.py to support Check-In, Select All, and Reset.Phase 3Dynamic Engine FilterUpdate MultiRallyAssignmentEngine to accept CHECKED_IN_PLAYER_IDS filters.Phase 4Web Admin UIRender check-in controls, "Select All", and "Clear Filters" buttons on the admin dashboard.Phase 5Table FormatterIntegrate ConsolidatedTableFormatter to output single-row player summaries with tactical notes.