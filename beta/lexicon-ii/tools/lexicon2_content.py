# lexicon2_content.py - the words of "Res React Lexicon II: Eighties-ism".
# Five decks x five grammar rows x eight columns = 200 cells.
# Every cell is (text, src): src is the EXACT term from TERMS_SOURCE.txt the cell
# is cut from (verbatim substring, checked at build), or None for an added
# broadcast-age word. Decks 2-5 sort the corpus per artistic register; deck 1
# MASTER mushes every register together and mops up what the registers missed.
# -*- coding: utf-8 -*-

A = None  # ADDED: 80s broadcast flavour, not from the source list

DECKS = ['Master', 'Ad Break', 'The Sermon', 'The Reel', 'La Nuit']

COLUMNS = {
 'Master':     ['This Is Not', 'Prime Time', 'Cathedral', 'Reel Change',
                'La Nuit', 'Lilac', 'Raison', 'Test Card'],
 'Ad Break':   ['Prime Time', 'Ad Break', 'Home Shopping', 'Laugh Track',
                'Infomercial', 'Ratings', 'Vidiot', 'Sign Off'],
 'The Sermon': ['Commandment', 'Truism', 'Confession', 'Warning',
                'Blessing', 'Curse', 'Litany', 'Amen'],
 'The Reel':   ['Attention', 'Kino Eye', 'October', 'Intertitle',
                'Caligari', 'Sunrise', 'Splice', 'The End'],
 'La Nuit':    ['Rrose', 'Esquimaux', 'Javel', 'Serre-Chaude',
                'Côte d’Azur', 'Quincaillerie', 'Belle', 'Éternèbre'],
}

# source-term shorthands (must match TERMS_SOURCE.txt byte-for-byte)
TV_DELIVERS = 'Television delivers people to an advertiser.'
CONSUMED    = 'It is the consumer who is consumed.'
FEARS       = 'Your oldest fears are your worst ones?!!!? ! Oh! Mother will be pleased'
VERTOV      = ('Attention viewers! This film is an experiment in the cinematic '
               'communication of real events: without the help of intertitles; without '
               'the help of a story; without the help of theatre. This experimental work '
               'aims at creating a truly international language of cinema based on its '
               'absolute separation from the language of theatre and literature.')
EPILOGUE    = ('Here our story should really end, for in actual life, the forlorn old '
               'man would have little to look forward to but death. The author took pity '
               'on him, however, and provided quite an improbable epilogue.')
SONG        = ('This song of the Man and his Wife is of no place and every place. '
               'You might hear it anywhere at any time.')
OCTOBER     = 'Yesterday, Today, Tomorrow. A Film Poem Dedicated to the October Celebrations.'
SOVIET      = 'You are the owners of the Soviet land / in your hands lies a sixth part of the world'
REINDEER    = 'You who eat the meat of reindeer / dipping it into warm blood'
GRAPES      = 'You with your grapes / you with your rice'
SUCKLE      = 'You, who suckle at your mother’s breast / and you, hale 100-year-old'
MEDIATOR    = 'The mediator between the head and the hands must be the heart.'
ABUSE       = 'Abuse of power comes as no surprise'
PROPERTY    = 'Private property created crime'
PROTECT     = 'Protect me from what I want'
YOURWORLD   = 'IT’S YOUR WORLD, YOU CAN CHANGE IT'
LESDENTS    = 'Les dents des femmes sont des objets si charmants …'
QUONNE      = 'qu’on ne devrait les voir qu’en rêve ou à l’instant de l’amour.'
AVEZ        = 'Avez-vous déjà mis la moëlle de l’épée dans le poêle de l’aimée ?'
BAINS       = 'Bains de gros thé pour grains de beauté sans trop de bengué.'
ESQUIVONS   = 'Esquivons les ecchymoses des Esquimaux aux mots exquis.'
ASPIRANT    = 'L’aspirant habite Javel et moi j’avais l’habite en spirale.'
ENFANT      = ('L’enfant qui tète est un souffleur de chair chaude et n’aime pas '
               'le chou-fleur de serre-chaude.')
MOUSTIQUES  = ('On demande des moustiques domestiques (demi-stock) pour la cure '
               'd’azote sur la Côte d’Azur.')
ROBINET     = ('Parmi nos articles de quincaillerie paresseuse, nous recommandons le '
               'robinet qui s’arrête de couler quand on ne l’écoute pas.')
CISEAUX     = 'Si je te donne un sou, me donneras-tu une paire de ciseaux ?'
ETERNEBRE   = 'Nous sommes à jamais perdus dans le désert de l’éternèbre.'
BELLE_EST   = 'Qu’elle est belle.'
BELLE_ETAIT = 'Qu’elle était belle.'
FLEUR       = 'Belle, belle comme une fleur de verre.'
ANEMIC      = 'A – turn – ME – turn – RI – turn – C …'
LANDSCAPE   = 'This is a glimpse of the video landscape of tomorrow…'
NEWSPRINT   = 'This is a newsprint photo / of a photograph / of a videotape.'
TITLEFILM   = 'This is the title of this film. The rest will look just like this.'

# GRID[deck][row] = 8 x (text, src). Rows: Subject / Verb / Object / Mark / Field.
GRID = {

'Master': {
 'Subject': [
   ('AMERICA', 'America'),
   ('TELEVISION', TV_DELIVERS),
   ('EVERY ARTIST', 'EVERY ARTIST IS A CANNIBAL'),
   ('HEAT', 'HEAT IS LIFE'),
   ('THE UNEMPLOYED', 'ARM THE UNEMPLOYED'),
   ('LIBERTY', 'USA WHERE LIBERTY IS A STATUE'),
   ('ELLE', BELLE_EST),
   ('YOUR OLDEST FEARS', FEARS)],
 'Verb': [
   ('IS', 'EVERYTHING YOU KNOW IS WRONG'),
   ('IS NOT', 'This Is Not America'),
   ('WATCHED', A),
   ('PROTECT ME FROM', PROTECT),
   ('CAN CHANGE', YOURWORLD),
   ('SHAKE', 'Shake thy Wonder Maker'),
   ('CALL', 'Call your mother'),
   ('ARM', 'ARM THE UNEMPLOYED')],
 'Object': [
   ('AMERICA’S FLAG', 'This Is Not America’s Flag'),
   ('A STATUE', 'USA WHERE LIBERTY IS A STATUE'),
   ('A CANNIBAL', 'EVERY ARTIST IS A CANNIBAL'),
   ('LIFE', 'HEAT IS LIFE'),
   ('YOUR MOTHER', 'Call your mother'),
   ('WHAT I WANT', PROTECT),
   ('THY WONDER MAKER', 'Shake thy Wonder Maker'),
   ('YOUR WORLD', YOURWORLD)],
 'Mark': [
   ('THE END', 'A MOVIE / BRUCE CONNER / THE END'),
   ('RACE', 'RACE'),
   ('PRINCIPE / DÉVELOPPEMENT / PREUVE', 'PRINCIPE / DÉVELOPPEMENT / PREUVE'),
   ('G.P.O. / Cheaper Parcel Post', 'G.P.O. / Cheaper Parcel Post'),
   ('IT COULD NEVER HAPPEN HERE', 'IT COULD NEVER HAPPEN HERE'),
   ('DEATH IS INEVITABLE', 'DEATH IS INEVITABLE'),
   ('EVOLUTION IS OVER', 'EVOLUTION IS OVER'),
   ('ENTRANCE / EXIT', 'ENTRANCE / EXIT')],
 'Field': [
   ('REASON OVER PASSION / LA RAISON AVANT LA PASSION',
    'REASON OVER PASSION / LA RAISON AVANT LA PASSION'),
   ('A blooming lilac in early light. Scene brightens slowly.',
    'A blooming lilac in early light. Scene brightens slowly.'),
   ('For some reason she is embarrassed about her reverie.',
    'For some reason she is embarrassed about her reverie.'),
   ('Wander through large quiet rooms.', 'Wander through large quiet rooms.'),
   (NEWSPRINT, NEWSPRINT),
   (TITLEFILM, TITLEFILM),
   ('I’d like to teach the world to sing', 'I’d like to teach the world to sing'),
   (LANDSCAPE, LANDSCAPE)],
},

'Ad Break': {
 'Subject': [
   ('TELEVISION', TV_DELIVERS),
   ('MONEY', 'Money creates taste'),
   ('THE CONSUMER', CONSUMED),
   ('CELEBRITY', 'CELEBRITY IS A JOB'),
   ('THE SINGLES MARKET', 'WE ARE THE TARGET OF THE SINGLES MARKET'),
   ('AMBITION', 'AMBITION BITES THE NAILS OF SUCCESS'),
   ('REBELLION', 'REBELLION IS PACKAGED'),
   ('EVERYTHING YOU KNOW', 'EVERYTHING YOU KNOW IS WRONG')],
 'Verb': [
   ('WATCHES', A),
   ('SELLS', A),
   ('DELIVERS', TV_DELIVERS),
   ('CREATES', 'Money creates taste'),
   ('BITES', 'AMBITION BITES THE NAILS OF SUCCESS'),
   ('INTERRUPTS', A),
   ('SPONSORS', A),
   ('IS', 'EVERYTHING YOU KNOW IS WRONG')],
 'Object': [
   ('PEOPLE', TV_DELIVERS),
   ('AN ADVERTISER', TV_DELIVERS),
   ('TASTE', 'Money creates taste'),
   ('THE REAL THING', "It's the real thing"),
   ('A JOB', 'CELEBRITY IS A JOB'),
   ('THE NAILS OF SUCCESS', 'AMBITION BITES THE NAILS OF SUCCESS'),
   ('THE SURFACE', 'ENJOY THE SURFACE'),
   ('WRONG', 'EVERYTHING YOU KNOW IS WRONG')],
 'Mark': [
   ('I will not make any more boring art.', 'I will not make any more boring art.'),
   ('LIE', 'LIE'),
   ('?!!!? !', FEARS),
   ('R U A VIDIOT?', 'R U A VIDIOT?'),
   ('SERVICE NOT INCLUDED', 'SERVICE NOT INCLUDED'),
   ('THIS IS NOT AN ADVERTISEMENT', 'THIS IS NOT AN ADVERTISEMENT'),
   ('We Will Rock You', 'We Will Rock You'),
   ("It's the real thing", "It's the real thing")],
 'Field': [
   ('WATCH MORE TV', 'WATCH MORE TV'),
   ('CONSUME LATER', 'CONSUME LATER'),
   ('BELIEVE EVERYTHING', 'BELIEVE EVERYTHING'),
   ('ENJOY THE SURFACE', 'ENJOY THE SURFACE'),
   ('WE ARE THE TARGET OF THE SINGLES MARKET',
    'WE ARE THE TARGET OF THE SINGLES MARKET'),
   (CONSUMED, CONSUMED),
   ('I’m not trying to sell you anything.', 'I’m not trying to sell you anything.'),
   ('You are the product of TV.', 'You are the product of TV.')],
},

'The Sermon': {
 'Subject': [
   ('TASTE', 'TASTE IS THE ENEMY OF ART'),
   ('SUPERFICIALITY', 'SUPERFICIALITY IS GOD'),
   ('PANIC', 'PANIC IS ATTITUDE'),
   ('PEACE', 'PEACE IS A LUXURY'),
   ('RELIGION', 'RELIGION IS A CLUB'),
   ('IGNORANCE', 'IGNORANCE IS BLISS'),
   ('GUILT', 'GUILT IS NOT OF GOD'),
   ('THE FUTURE', 'THE FUTURE IS A FANTASY')],
 'Verb': [
   ('IS', 'TASTE IS THE ENEMY OF ART'),
   ('IS NOT', 'GUILT IS NOT OF GOD'),
   ('HAS FAILED', 'SCIENCE HAS FAILED'),
   ('COMES AS', ABUSE),
   ('CREATED', PROPERTY),
   ('BELIEVES IN', A),
   ('FORGIVES', A),
   ('WANTS', A)],
 'Object': [
   ('THE ENEMY OF ART', 'TASTE IS THE ENEMY OF ART'),
   ('A LUXURY', 'PEACE IS A LUXURY'),
   ('A CLUB', 'RELIGION IS A CLUB'),
   ('BLISS', 'IGNORANCE IS BLISS'),
   ('NO SURPRISE', ABUSE),
   ('A CAREER MOVE', 'DEATH IS A CAREER MOVE'),
   ('A FANTASY', 'THE FUTURE IS A FANTASY'),
   ('CRIME', PROPERTY)],
 'Mark': [
   ('GOD', 'SUPERFICIALITY IS GOD'),
   ('LOVE', 'LOVE'),
   ('HATE', 'HATE'),
   ('WIN', 'WIN'),
   ('SELL', 'SELL'),
   ('STEAL', 'STEAL'),
   ('CHEAT', 'CHEAT'),
   ('WHO CARES', 'WHO CARES')],
 'Field': [
   ('AVOID CONFLICT', 'AVOID CONFLICT'),
   ('MAKE FRIENDS', 'MAKE FRIENDS'),
   ('CRY MORE OFTEN', 'CRY MORE OFTEN'),
   ('TREAD SOFTLY', 'TREAD SOFTLY'),
   ('POST EARLY', 'POST EARLY'),
   ('STARVE', 'STARVE'),
   ('SPEED', 'SPEED'),
   ('housing is a human right', 'housing is a human right')],
},

'The Reel': {
 'Subject': [
   ('THIS FILM', VERTOV),
   ('THE MAN AND HIS WIFE', SONG),
   ('THE FORLORN OLD MAN', EPILOGUE),
   ('THE AUTHOR', EPILOGUE),
   ('YOU WHO EAT THE MEAT OF REINDEER', REINDEER),
   ('YOU WITH YOUR GRAPES', GRAPES),
   ('THE OWNERS OF THE SOVIET LAND', SOVIET),
   ('YOU, WHO SUCKLE', SUCKLE)],
 'Verb': [   # past tense throughout - agreement-neutral, intertitle register
   ('PROVIDED', EPILOGUE),
   ('TOOK PITY ON', EPILOGUE),
   ('MUST BE', MEDIATOR),
   ('MIGHT HEAR', SONG),
   ('REWOUND', A),
   ('PROJECTED', A),
   ('SPLICED', A),
   ('DISSOLVED INTO', A)],
 'Object': [
   ('THE HEART', MEDIATOR),
   ('A SIXTH PART OF THE WORLD', SOVIET),
   ('AN IMPROBABLE EPILOGUE', EPILOGUE),
   ('THE LANGUAGE OF THEATRE', VERTOV),
   ('WARM BLOOD', REINDEER),
   ('THE OCTOBER CELEBRATIONS', OCTOBER),
   ('A FILM POEM', OCTOBER),
   ('REAL EVENTS', VERTOV)],
 'Mark': [
   ('THE END', 'A MOVIE / BRUCE CONNER / THE END'),
   ('Once upon a time', 'Once upon a time'),
   ('Suddenly…', 'Suddenly…'),
   ('Eight years later', 'Eight years later'),
   ('Sixteen years before', 'Sixteen years before'),
   ('Around three in the morning', 'Around three in the morning'),
   ('In spring', 'In spring'),
   ('Du musst Caligari werden', 'Du musst Caligari werden')],
 'Field': [
   ('splice', 'splice'),
   ('incision', 'incision'),
   ('screen', 'screen'),
   ('space', 'space'),
   ('FRAGMENTATION', 'FRAGMENTATION'),
   ('SUBLIMINAL', 'SUBLIMINAL'),
   ('SAILBOAT', 'SAILBOAT'),
   ('A map of ideas', 'A map of ideas')],
},

'La Nuit': {
 # 3sg throughout except column 0, which is the deck's one plural column and is
 # column-aligned so its own fire reads whole: LES DENTS DES FEMMES SONT DES
 # OBJETS SI CHARMANTS. Cross-fires into col 0 are dada on purpose.
 'Subject': [
   ('LES DENTS DES FEMMES', LESDENTS),
   ('L’ASPIRANT', ASPIRANT),
   ('L’ENFANT QUI TÈTE', ENFANT),
   ('LE ROBINET', ROBINET),
   ('LA MOËLLE DE L’ÉPÉE', AVEZ),
   ('LE DÉSERT', ETERNEBRE),
   ('ELLE', BELLE_EST),
   ('UNE FLEUR DE VERRE', FLEUR)],
 'Verb': [
   ('SONT', LESDENTS),
   ('EST', BELLE_EST),
   ('ÉTAIT', BELLE_ETAIT),
   ('HABITE', ASPIRANT),
   ('DONNE', CISEAUX),
   ('TÈTE', ENFANT),
   ('DEMANDE', MOUSTIQUES),
   ('N’AIME PAS', ENFANT)],
 'Object': [
   ('DES OBJETS SI CHARMANTS', LESDENTS),
   ('JAVEL', ASPIRANT),
   ('LE CHOU-FLEUR DE SERRE-CHAUDE', ENFANT),
   ('DES MOUSTIQUES DOMESTIQUES', MOUSTIQUES),
   ('UNE PAIRE DE CISEAUX', CISEAUX),
   ('LES ECCHYMOSES DES ESQUIMAUX', ESQUIVONS),
   ('GRAINS DE BEAUTÉ', BAINS),
   ('LE DÉSERT DE L’ÉTERNÈBRE', ETERNEBRE)],
 'Mark': [
   ('Adieu.', 'Adieu.'),
   ('Vous ne rêvez pas.', 'Vous ne rêvez pas.'),
   (BELLE_EST, BELLE_EST),
   ('beLIEve', 'beLIEve → LIE'),
   ('vanishing points', 'vanishing points → points vanishing'),
   ('duck / hormone / chrome', 'duck / hormone / chrome'),
   (ANEMIC, ANEMIC),
   ('l’instant de l’amour', QUONNE)],
 'Field': [
   (AVEZ, AVEZ),
   (BAINS, BAINS),
   (ESQUIVONS, ESQUIVONS),
   (ENFANT, ENFANT),
   (MOUSTIQUES, MOUSTIQUES),
   (ROBINET, ROBINET),
   (CISEAUX, CISEAUX),
   (ASPIRANT, ASPIRANT)],
},
}
