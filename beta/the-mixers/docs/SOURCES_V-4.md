# Edirol (Roland) V-4: sourced facts

Gathered 2026-10-23 for the V-4 deck. Every caption on that deck comes from a line here.

Sources: [RL] https://proav.roland.com/products/v-4/ · [OM] Owner's Manual, 108 pp, https://www.manualsdir.com/manuals/80319/edirol-4-channel-v-4.html (append `?page=N`) · [VM] Videomaker review https://www.videomaker.com/article/9990-video-mixer-review-edirol-v-4/ · [MC] MIDI Implementation Chart scan https://mcgrp.ru/files/viewer/5687/84 · [CDM] https://cdm.link/v-4-video-mixer-now-hdmi-first-look-at-rolands-v-4ex/ · [VG] https://www.videoguys.com/blogs/news-and-sales/25-years-of-roland-video-switchers · [PR] https://proav.roland.com/de/news_events/press_releases/2013/2489/

## Identity
- Edirol (Roland); introduced 2002, aimed at video DJs [VG]; MIDI chart dated 13 Dec 2002 v1.00 [MC]; now discontinued [RL]
- 225 (W) x 295 (D) x 105 (H) mm, 2.3 kg [RL]
- $1,195 street in Videomaker's 2004 review [VM]; 2002 launch MSRP not found
- Club World Awards "Best Video Product 2004" [RL]
- Successor V-4EX shown at ISE 2013, release March 2013; Roland calls the V-4 "the industry-standard" [PR]
- AC adaptor, 1500 mA; box includes 4 spare T-bar screws [RL][OM p.83]

## Inputs / outputs
- 4 composite inputs (RCA); S-Video on inputs 1 and 2 (takes priority when both connected) [RL][OM p.83]
- Program out: 2 x composite RCA + 1 x S-Video; preview out: 1 x composite [RL][VM]
- Two independent frame synchronizers (2-channel TBC); no genlock [RL][OM p.10]
- No audio at all: "The V4 does not have audio inputs so will not mix audio" [OM p.17]
- MIDI IN and MIDI OUT, 5-pin DIN; THRU is a soft option on OUT [OM p.83, p.89]

## Front panel
- Channel A and Channel B buses, input select buttons 1-4 on each [OM p.15]
- T-bar video fader, "over 100 steps", mountable horizontal or vertical [OM p.16][RL]
- Transition buttons MIX, WIPE, EFX [OM p.15]; over 200 wipe types (hard, soft, multi-border) [OM p.83]; Videomaker counts 216 wipes, 4 keyed transitions, 27 slides [VM]
- Channel A effect buttons: Strobe, Negative, Colorize, Multi; Channel B: Mirror, Chroma Key, Luminance Key, P in P [OM p.15-16]
- Full effect list: Strobe, Still, Negative, Colorize, Solarization, Mirror, Multi, Shake; compositing: PIP, Luminance Key, Chroma Key [OM p.83]
- TRANSFORMER buttons per channel: cut between A and B without the fader [OM p.15, p.51]
- BPM display, BPM CONTROL dial, TAP button, BPM SYNC button: switches A/B or toggles effects on the beat "without you having to operate the video fader" [OM p.14-15, p.37]
- OUTPUT FADE dial: left fades to black, right to white [OM p.14, p.46]
- 8 panel memories on the MEMORY dial (no. 1 is factory) [OM p.15][RL]
- NTSC / PAL chosen in the menu [OM p.71]

## MIDI
- Note On selects inputs (Note Mode on): A1-A4 = notes 36, 38, 40, 41; B1-B4 = 43, 45, 47, 48 [OM p.89][MC]
- Program Change: bank 50H + PC 0-7 = memory 1-8; bank 00H + PC 0-3 = A input; bank 01H + PC 0-3 = B input [OM p.89]
- Assignable CCs 1-5, 7-31, 64-95; transition time defaults to CC7 (0-127 = 0.0-4.0 s) [OM p.89, p.94]
- MIDI clock F8 drives BPM SYNC; Start FA / Continue FB mark the downbeat [OM p.90]
- SysEx received only (Roland ID 41H, model 00H 51H) [OM p.90][MC]
- V-LINK: the partner device puts the V-4 into Presentation mode [OM p.58][RL]; MIDI Visual Control not found (predates it)

## Technical
- NTSC or PAL (ITU-601); 13.5 MHz, 4:2:2, 8-bit, fully digital [RL][OM p.83]
- Latency: not documented

## Quotable
- "For years, the Roland V-4 was the battle axe of the VJ and visual performance scene." [CDM]
- "Not owning one almost meant you weren't serious about playing." [CDM]
- "it really wants to strut its stuff on the dance floor" [VM]
- "the industry-standard Roland V-4" [PR]

## Not found
2002 launch price; measured latency; fade to a colour other than black/white; MVC; genlock.
