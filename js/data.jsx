/* Données : spectacles, ateliers, agenda, équipe, partenaires */
const SPECTACLES = [
  { id:"gens-de-peu", num:"01", title:"Les Gens de peu", tag:"Théâtre", date:"Mai – Juin 2026", duration:"1h20", ages:"Dès 14 ans", color:"#B84A2E", textColor:"#F4E8D5", desc:"Un chant choral pour ceux qu'on n'écoute jamais. Cinq voix, cinq corps, cinq territoires de la France ordinaire qui s'entrelacent dans une polyphonie tendre et féroce.", auteur:"Pierre Michon, adaptation collective", mes:"Camille Vasseur", with:"Léa Bonnet, Karim Toulousi, Nadia Pereira, Vincent Doré, Sami Khaled" },
  { id:"corps-a-corps", num:"02", title:"Corps à corps", tag:"Danse-théâtre", date:"Avril 2026", duration:"55 min", ages:"Tout public", color:"#9B7AA8", textColor:"#F4E8D5", desc:"Un duo où le geste précède le mot. Deux interprètes négocient l'espace entre eux comme on négocie l'amour : par retrait, par offre, par malentendu.", auteur:"Création collective", mes:"Ines Falcón & Bastien Roy", with:"Ines Falcón, Bastien Roy" },
  { id:"foret-imaginaire", num:"03", title:"La forêt imaginaire", tag:"Jeune public", date:"Saison 2025–26", duration:"45 min", ages:"Dès 6 ans", color:"#E8B542", textColor:"#3A1B2E", desc:"Une enfant entre dans la forêt et la forêt entre en elle. Un conte initiatique pour petits et grands, mêlant marionnette, ombre et chant.", auteur:"Théo Marquet", mes:"Théo Marquet", with:"Mira Solano, Théo Marquet" },
  { id:"frontieres", num:"04", title:"Aux frontières du réel", tag:"Création", date:"Septembre 2026", duration:"1h40", ages:"Dès 12 ans", color:"#3A1B2E", textColor:"#F4E8D5", desc:"Trois récits de seuils — la veille, le rêve, la mort — entrelacés en un seul mouvement. Création 2026 de la compagnie.", auteur:"Camille Vasseur", mes:"Camille Vasseur", with:"Distribution en cours" },
  { id:"ravages", num:"05", title:"Ravages", tag:"Théâtre", date:"Reprise mars 2026", duration:"1h10", ages:"Dès 16 ans", color:"#8E3620", textColor:"#F4E8D5", desc:"Un huis clos contemporain sur la mémoire qu'on s'invente. Reprise du succès de la saison 2024.", auteur:"Violette Marsan", mes:"Camille Vasseur", with:"Léa Bonnet, Vincent Doré" },
  { id:"voix-bois", num:"06", title:"La voix dans le bois", tag:"Conte musical", date:"Tournée juin 2026", duration:"50 min", ages:"Dès 4 ans", color:"#C89420", textColor:"#3A1B2E", desc:"Conte musical en plein air. Quatre musiciennes-comédiennes cheminent avec le public à travers un parc.", auteur:"D'après les contes des Pyrénées", mes:"Mira Solano", with:"Quatuor des Voix vives" },
];

const AGENDA = [
  { day:"14", month:"Mar", year:"2026", title:"Les Gens de peu", venue:"Théâtre du Garage, Toulon", time:"20h30", price:"12 / 18 €", spectacle:"gens-de-peu", status:"available", type:"spectacle" },
  { day:"15", month:"Mar", year:"2026", title:"Les Gens de peu", venue:"Théâtre du Garage, Toulon", time:"20h30", price:"12 / 18 €", spectacle:"gens-de-peu", status:"few", type:"spectacle" },
  { day:"22", month:"Mar", year:"2026", title:"Ravages", venue:"La Criée, Marseille", time:"21h00", price:"15 / 22 €", spectacle:"ravages", status:"available", type:"spectacle" },
  { day:"25", month:"Mar", year:"2026", title:"Stage de théâtre — vacances printemps", venue:"Filature de l'Isle, Périgueux", time:"10h — 17h", price:"90 € / 4 jours", status:"available", type:"atelier", cardColor:"#9B7AA8", cardTextColor:"#F4E8D5" },
  { day:"04", month:"Avr", year:"2026", title:"Corps à corps", venue:"Le Liberté, Toulon", time:"19h30", price:"10 / 15 €", spectacle:"corps-a-corps", status:"available", type:"spectacle" },
  { day:"05", month:"Avr", year:"2026", title:"Corps à corps", venue:"Le Liberté, Toulon", time:"19h30", price:"10 / 15 €", spectacle:"corps-a-corps", status:"sold", type:"spectacle" },
  { day:"12", month:"Avr", year:"2026", title:"La forêt imaginaire", venue:"Médiathèque, Hyères", time:"15h00", price:"Gratuit", spectacle:"foret-imaginaire", status:"available", type:"spectacle" },
  { day:"20", month:"Avr", year:"2026", title:"Résidence — Aux frontières du réel", venue:"Théâtre Liberté, Toulon", time:"Répétitions fermées", price:"Ouverture vendredi soir", status:"free", type:"résidence", cardColor:"#3A1B2E", cardTextColor:"#F4E8D5" },
  { day:"03", month:"Mai", year:"2026", title:"Les Gens de peu", venue:"Le Cratère, Alès", time:"20h00", price:"14 / 22 €", spectacle:"gens-de-peu", status:"available", type:"spectacle" },
  { day:"10", month:"Mai", year:"2026", title:"Rencontre avec l'équipe artistique", venue:"Filature de l'Isle, Périgueux", time:"18h00", price:"Entrée libre", status:"free", type:"événement", cardColor:"#E8B542", cardTextColor:"#3A1B2E" },
  { day:"17", month:"Mai", year:"2026", title:"La forêt imaginaire", venue:"Festival Off, Avignon", time:"11h00", price:"8 / 14 €", spectacle:"foret-imaginaire", status:"few", type:"spectacle" },
  { day:"18", month:"Mai", year:"2026", title:"La forêt imaginaire", venue:"Festival Off, Avignon", time:"11h00", price:"8 / 14 €", spectacle:"foret-imaginaire", status:"available", type:"spectacle" },
  { day:"30", month:"Mai", year:"2026", title:"Stage adultes — jeu et improvisation", venue:"Filature de l'Isle, Périgueux", time:"10h — 18h", price:"120 € / week-end", status:"few", type:"atelier", cardColor:"#3A1B2E", cardTextColor:"#F4E8D5" },
  { day:"08", month:"Juin", year:"2026", title:"La voix dans le bois", venue:"Parc du Mugel, La Ciotat", time:"18h30", price:"Libre", spectacle:"voix-bois", status:"available", type:"spectacle" },
  { day:"14", month:"Juin", year:"2026", title:"Restitution publique — Ateliers 2025-26", venue:"Filature de l'Isle, Périgueux", time:"17h00", price:"Entrée libre", status:"free", type:"événement", cardColor:"#B84A2E", cardTextColor:"#F4E8D5" },
  { day:"22", month:"Juin", year:"2026", title:"La voix dans le bois", venue:"Domaine du Rayol", time:"19h00", price:"Libre", spectacle:"voix-bois", status:"few", type:"spectacle" },
  { day:"29", month:"Juin", year:"2026", title:"Résidence d'été — Corps à corps", venue:"Domaine de Roquerpertuse", time:"Résidence fermée", price:"Lecture publique le 3 juil.", status:"free", type:"résidence", cardColor:"#9B7AA8", cardTextColor:"#F4E8D5" },
  { day:"12", month:"Sep", year:"2026", title:"Aux frontières du réel", venue:"Création — Théâtre Liberté", time:"20h30", price:"15 / 25 €", spectacle:"frontieres", status:"available", type:"spectacle" },
];

const ATELIERS = [
  { num:"A1", title:"Théâtre Enfants & Ados", who:"6–9 ans / 10–14 ans", when:"Mercredi 14h–15h30 / 16h–17h30", where:"Filature de l'Isle, Périgueux", price:"Adhésion + 60 € / trimestre", color:"#B84A2E", textColor:"#F4E8D5", desc:"Raconter une histoire en mettant en jeu son corps et sa voix. Observer le monde et le traduire scéniquement. Rendre visible l'invisible et oser être présent à soi et aux autres. Sorties aux spectacles incluses. Avec Perrine Marillier.", audience:"enfants" },
  { num:"A2", title:"Cycle d'expérimentation artistique", who:"Adultes", when:"1 samedi par mois, 9h45–16h", where:"Filature de l'Isle, Périgueux", price:"Adhésion + 75 € / trimestre", color:"#3A1B2E", textColor:"#F4E8D5", desc:"Cycle de découvertes, de pratiques et d'expérimentations artistiques. Sorties aux spectacles incluses. Avec Perrine Marillier, Mathieu Duval et Guilhem Loupiac.", audience:"adultes" },
  { num:"A3", title:"Compagnon Vocal", who:"Tous niveaux", when:"Mercredi tous les 15 jours, 11h30–13h", where:"Filature de l'Isle, Périgueux", price:"Adhésion – Gratuit", color:"#E8B542", textColor:"#3A1B2E", desc:"Venez chanter, écouter, vous ressourcer, vibrer. Aucune expérience vocale nécessaire. Avec Claude Danielle Morlet et Dominique Borie-Lagarde.", audience:"adultes" },
  { num:"A4", title:"Expression créatrice", who:"Tous publics", when:"Mardi 14h–16h", where:"Filature de l'Isle, Périgueux", price:"Adhésion – Gratuit", color:"#C89420", textColor:"#3A1B2E", desc:"Atelier d'expérimentation et de création plastique. Explorer sa créativité et son propre imaginaire en groupe. Pratique individuelle, création collective. Sans prérequis technique. Avec Ambre Ludwiczak.", audience:"adultes" },
  { num:"A5", title:"Rdv's du Toulon", who:"Habitants du quartier", when:"Jeudi 14h–16h", where:"Salle du 800 – EVS, Périgueux", price:"Adhésion – Gratuit", color:"#8E3620", textColor:"#F4E8D5", desc:"Rencontres interculturelles & créations collectives : Café Culture, médiations autour des spectacles, ateliers… + Sorties aux spectacles.", audience:"quartier" },
  { num:"A6", title:"Ateliers Geste", who:"8–12 ans", when:"21,28/04 — 5,12,19,26/05 — 2,9,16/06/2026 · 17h30–19h", where:"Odyssée, Périgueux", price:"Gratuit", color:"#9B7AA8", textColor:"#F4E8D5", desc:"Créer et jouer à la frontière du réel et du fantastique. Cycle de 9 séances avec Guilhem Loupiac. En partenariat avec L'Odyssée.", audience:"enfants" },
];

const EQUIPE = [
  { name:"Émilie Esquerré", role:"Comédienne, metteuse en scène", bio:"Rejoint la Cie Rouletabille en 2024-2025 avec une ligne artistique centrée sur la déconstruction des stéréotypes de genre et la critique des systèmes patriarcaux, en écho aux luttes sociales actuelles. « Pour apporter ma petite goutte au moulin de la déconstruction, je passe par le théâtre. »" },
  { name:"Perrine Marillier", role:"Intervenante artistique, chargée de communication", bio:"Anime les ateliers Théâtre Enfants & Ados et co-encadre le Cycle d'expérimentation artistique adultes. Pilier de la médiation artistique au quotidien." },
  { name:"Guilhem Loupiac", role:"Intervenant artistique — Ateliers Geste", bio:"Anime les Ateliers Geste pour les 8–12 ans en partenariat avec L'Odyssée, et participe au Cycle d'expérimentation artistique adultes." },
  { name:"Mathieu Duval", role:"Intervenant artistique", bio:"Co-encadre le Cycle d'expérimentation artistique adultes avec Perrine Marillier et Guilhem Loupiac." },
  { name:"Ambre Ludwiczak", role:"Intervenante — Expression créatrice", bio:"Anime l'atelier Expression créatrice, centré sur les arts plastiques et l'exploration de l'imaginaire. Approche libre et sans prérequis." },
  { name:"Claude Danielle Morlet", role:"Intervenante — Compagnon Vocal", bio:"Co-anime le Compagnon Vocal avec Dominique Borie-Lagarde. Un espace pour chanter, écouter, se ressourcer — ouvert à tous les niveaux." },
  { name:"Dominique Borie-Lagarde", role:"Intervenante — Compagnon Vocal", bio:"Co-anime le Compagnon Vocal. Pratique collective douce, aucune expérience vocale nécessaire." },
  { name:"L'administratrice", role:"Administration & gestion", bio:"Pilote l'administratif et la vie associative. Garante de la bonne santé financière et organisationnelle de la compagnie." },
];

const PARTENAIRES = [
  { name:"Région Nouvelle-Aquitaine", type:"Soutien institutionnel" },
  { name:"Agence Culturelle de la Dordogne", type:"Soutien institutionnel" },
  { name:"DRAC Nouvelle-Aquitaine", type:"Soutien institutionnel" },
  { name:"Département de la Dordogne", type:"Soutien institutionnel" },
  { name:"Ville de Périgueux", type:"Soutien institutionnel" },
  { name:"L'Odyssée", type:"Partenaires artistiques" },
  { name:"Cie Lilo", type:"Partenaires artistiques" },
  { name:"Cie du Grand Doute", type:"Partenaires artistiques" },
  { name:"Cie Pittoresque", type:"Partenaires artistiques" },
  { name:"Cie 3G", type:"Partenaires artistiques" },
  { name:"Cie Anandi", type:"Partenaires artistiques" },
  { name:"Cie Structure", type:"Partenaires artistiques" },
  { name:"Le Sans Réserve", type:"Action culturelle & territoire" },
  { name:"Maison 24", type:"Action culturelle & territoire" },
  { name:"Maison pour Tous", type:"Action culturelle & territoire" },
  { name:"Centre social St Exupéry", type:"Action culturelle & territoire" },
  { name:"Centre social l'Arche", type:"Action culturelle & territoire" },
  { name:"UPOP24", type:"Action culturelle & territoire" },
  { name:"Conseil Citoyen Chamiers", type:"Action culturelle & territoire" },
  { name:"APF24", type:"Action culturelle & territoire" },
  { name:"UEMO PJJ", type:"Action culturelle & territoire" },
  { name:"CADA FTA", type:"Action culturelle & territoire" },
  { name:"APARE", type:"Action culturelle & territoire" },
  { name:"Hestia", type:"Action culturelle & territoire" },
  { name:"Orizon", type:"Action culturelle & territoire" },
  { name:"Commune de Mensignac", type:"Action culturelle & territoire" },
  { name:"Lycée Léonard de Vinci", type:"Éducation" },
  { name:"Collège Clos Chassaing", type:"Éducation" },
  { name:"IUT de Périgueux", type:"Éducation" },
  { name:"Ligue de l'Enseignement", type:"Éducation" },
  { name:"Ciné Cinéma", type:"Éducation" },
];

export { SPECTACLES, AGENDA, ATELIERS, EQUIPE, PARTENAIRES };
