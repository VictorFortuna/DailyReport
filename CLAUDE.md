# DailyReport Project Instructions

- All screenshots are stored in /mnt/d/Projects/DailyReport/screens. When the user says 'посмотри' (look), 'смотри' (look), or similar viewing commands without specifying what to look at, they are referring to screenshots in this folder. When the user describes something that is difficult to explain in words but easier to understand visually (UI/UX issues, design problems, layout concerns), check the screenshots first.

## SCREENSHOT RULES

**CRITICAL RULES - ALWAYS FOLLOW:**

1. **Analyze BEFORE Acting**
   - When user shows a screenshot with markings (arrows, lines, circles, crosses), FULLY analyze ALL markings before making any changes
   - Identify EXACTLY what is marked: colors, positions, directions
   - DO NOT make assumptions or guess - look carefully at the visual information

2. **Ask When Unclear**
   - When user says "move left/right/up/down" without specific measurements, ask "by how much?" or "to which position?"
   - When there's ambiguity in the task, ask clarifying questions BEFORE acting
   - Better to ask once than to iterate multiple times with wrong implementations

3. **Confirm Understanding**
   - Before executing visual changes, confirm your understanding of the task
   - Example: "I understand you want to move the button 50px left to align with the blue line. Correct?"
   - Wait for confirmation if the task is complex or ambiguous

4. **Common Mistakes to AVOID**
   - Confusing horizontal/vertical lines
   - Missing the exact location of markings on screenshots
   - Guessing pixel values instead of asking
   - Starting work before fully understanding the visual requirements

## BOT DEVELOPMENT RULES

**Bot Restart Required:**
- Any changes to Python handlers require full bot restart (like browser refresh)
- Stop: Ctrl+C or `pkill -f run_bot`
- Start: `python3 run_bot.py`

**Dependencies:**
- Install: `pip3 install -r requirements.txt`
- Required modules: aiogram, aiohttp, APScheduler, aiosqlite

**Configuration:**
- Environment: `.env` file
- Time settings: `REMINDER_TIME=22:00`
- Admin ID: `ADMIN_TELEGRAM_ID=325463089`

## VISUAL WORKFLOW RULES

1. **Analyze BEFORE Acting** - examine ALL markings before making changes
2. **Ask When Unclear** - get specific measurements and positions  
3. **Confirm Understanding** - verify task before execution
4. **No Assumptions** - reference screenshots or ask for clarification
