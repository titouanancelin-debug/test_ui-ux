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
  { day:"14", month:"Mar", year:"2026", title:"Les Gens de peu", venue:"Théâtre du Garage, Toulon", time:"20h30", price:"12 / 18 €", spectacle:"gens-de-peu", status:"available" },
  { day:"15", month:"Mar", year:"2026", title:"Les Gens de peu", venue:"Théâtre du Garage, Toulon", time:"20h30", price:"12 / 18 €", spectacle:"gens-de-peu", status:"few" },
  { day:"22", month:"Mar", year:"2026", title:"Ravages", venue:"La Criée, Marseille", time:"21h00", price:"15 / 22 €", spectacle:"ravages", status:"available" },
  { day:"04", month:"Avr", year:"2026", title:"Corps à corps", venue:"Le Liberté, Toulon", time:"19h30", price:"10 / 15 €", spectacle:"corps-a-corps", status:"available" },
  { day:"05", month:"Avr", year:"2026", title:"Corps à corps", venue:"Le Liberté, Toulon", time:"19h30", price:"10 / 15 €", spectacle:"corps-a-corps", status:"sold" },
  { day:"12", month:"Avr", year:"2026", title:"La forêt imaginaire", venue:"Médiathèque, Hyères", time:"15h00", price:"Gratuit", spectacle:"foret-imaginaire", status:"available" },
  { day:"03", month:"Mai", year:"2026", title:"Les Gens de peu", venue:"Le Cratère, Alès", time:"20h00", price:"14 / 22 €", spectacle:"gens-de-peu", status:"available" },
  { day:"17", month:"Mai", year:"2026", title:"La forêt imaginaire", venue:"Festival Off, Avignon", time:"11h00", price:"8 / 14 €", spectacle:"foret-imaginaire", status:"few" },
  { day:"18", month:"Mai", year:"2026", title:"La forêt imaginaire", venue:"Festival Off, Avignon", time:"11h00", price:"8 / 14 €", spectacle:"foret-imaginaire", status:"available" },
  { day:"08", month:"Juin", year:"2026", title:"La voix dans le bois", venue:"Parc du Mugel, La Ciotat", time:"18h30", price:"Libre", spectacle:"voix-bois", status:"available" },
  { day:"22", month:"Juin", year:"2026", title:"La voix dans le bois", venue:"Domaine du Rayol", time:"19h00", price:"Libre", spectacle:"voix-bois", status:"few" },
  { day:"12", month:"Sep", year:"2026", title:"Aux frontières du réel", venue:"Création — Théâtre Liberté", time:"20h30", price:"15 / 25 €", spectacle:"frontieres", status:"available" },
];

const ATELIERS = [
  { num:"A1", title:"Théâtre Enfants", who:"6 — 11 ans", when:"Mercredi 14h — 16h", where:"Atelier rue Pierre Sémard", price:"60 € / trimestre", color:"#B84A2E", textColor:"#F4E8D5", desc:"Jeux de rôle, improvisation, premières scènes. Approche corporelle et joyeuse." },
  { num:"A2", title:"Théâtre Ados", who:"12 — 17 ans", when:"Vendredi 17h30 — 19h30", where:"Atelier rue Pierre Sémard", price:"75 € / trimestre", color:"#9B7AA8", textColor:"#F4E8D5", desc:"Travail sur texte contemporain, écriture de plateau, présentation publique en fin d'année." },
  { num:"A3", title:"Théâtre Adultes", who:"18 ans et +", when:"Un samedi par mois", where:"Atelier rue Pierre Sémard", price:"75 € / trimestre", color:"#3A1B2E", textColor:"#F4E8D5", desc:"Atelier mensuel intensif. Classiques revisités, improvisation longue, écoute du groupe." },
  { num:"A4", title:"Compagnon vocal", who:"Tous niveaux", when:"Tous les 15 jours", where:"Maison de quartier Pont-du-Las", price:"Gratuit (sur inscription)", color:"#E8B542", textColor:"#3A1B2E", desc:"Travail sur la voix parlée et chantée. Pratique collective douce, ouverte aux non-comédiens." },
  { num:"A5", title:"Expression créatrice", who:"Adultes en insertion", when:"Mardi 14h — 16h", where:"Centre social Beaucaire", price:"Gratuit", color:"#C89420", textColor:"#3A1B2E", desc:"En partenariat avec le CCAS. Médiation par le théâtre pour personnes en parcours." },
  { num:"A6", title:"Les Rdv du Toulon", who:"Habitants du quartier", when:"Jeudi 14h — 16h", where:"Itinérant", price:"Gratuit", color:"#8E3620", textColor:"#F4E8D5", desc:"Rendez-vous mensuels d'écriture collective avec les habitants. Restitution publique en juin." },
];

const EQUIPE = [
  { name:"Camille Vasseur", role:"Direction artistique, mise en scène", bio:"Formée au Conservatoire de Marseille. Fonde la compagnie en 2014 après dix ans de plateau. Travaille sur la mémoire intime et le récit collectif." },
  { name:"Mira Solano", role:"Comédienne, metteure en scène jeune public", bio:"Comédienne, marionnettiste. Spécialisée dans les formes pour le très jeune public et la médiation en milieu scolaire." },
  { name:"Théo Marquet", role:"Comédien, écriture", bio:"Auteur-comédien. Co-écrit les créations jeune public depuis 2019. Anime également les ateliers ados." },
  { name:"Léa Bonnet", role:"Comédienne", bio:"Joue avec la compagnie depuis 2018. Également formatrice voix sur l'atelier Compagnon vocal." },
  { name:"Vincent Doré", role:"Comédien, scénographie", bio:"Plasticien de formation, conçoit les scénographies depuis 2020. Joue dans Ravages et Les Gens de peu." },
  { name:"Ines Falcón", role:"Danseuse, chorégraphe", bio:"Vient de la danse contemporaine. Co-signe Corps à corps. Apporte un regard chorégraphique sur l'ensemble du répertoire." },
  { name:"Karim Toulousi", role:"Comédien, musique live", bio:"Comédien-musicien. Compose pour les créations de la compagnie depuis 2021." },
  { name:"Nadia Pereira", role:"Administration, production", bio:"Pilote l'administratif et la diffusion. Garante du projet artistique au quotidien." },
];

const PARTENAIRES = [
  { name:"DRAC PACA", type:"Soutien institutionnel" },
  { name:"Région Sud", type:"Soutien institutionnel" },
  { name:"Département du Var", type:"Soutien institutionnel" },
  { name:"Ville de Toulon", type:"Soutien institutionnel" },
  { name:"Théâtre Liberté", type:"Coproduction" },
  { name:"La Criée", type:"Coproduction" },
  { name:"Le Cratère, Alès", type:"Coproduction" },
  { name:"Festival d'Avignon Off", type:"Diffusion" },
  { name:"CCAS de Toulon", type:"Action culturelle" },
  { name:"Maison de quartier Pont-du-Las", type:"Action culturelle" },
  { name:"Centre social Beaucaire", type:"Action culturelle" },
  { name:"ADAMI", type:"Soutien" },
];

window.SPECTACLES = SPECTACLES;
window.AGENDA = AGENDA;
window.ATELIERS = ATELIERS;
window.EQUIPE = EQUIPE;
window.PARTENAIRES = PARTENAIRES;
