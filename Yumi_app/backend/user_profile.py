# user_profile.py - Gestion des profils utilisateurs pour personnaliser les scores YUmi

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional

class AgeGroup(Enum):
    CHILD = "child"          # 3-12 ans
    TEENAGER = "teenager"    # 13-17 ans
    ADULT = "adult"          # 18-64 ans
    SENIOR = "senior"        # 65+ ans

class ActivityLevel(Enum):
    SEDENTARY = "sedentary"      # Peu d'activité
    LIGHT = "light"              # Activité légère
    MODERATE = "moderate"        # Activité modérée
    ACTIVE = "active"            # Très actif
    VERY_ACTIVE = "very_active"  # Extrêmement actif

class DietaryRestriction(Enum):
    NONE = "none"
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    GLUTEN_FREE = "gluten_free"
    LACTOSE_FREE = "lactose_free"
    HALAL = "halal"
    KOSHER = "kosher"
    LOW_SODIUM = "low_sodium"
    DIABETIC = "diabetic"

class HealthGoal(Enum):
    MAINTAIN_WEIGHT = "maintain_weight"
    LOSE_WEIGHT = "lose_weight"
    GAIN_WEIGHT = "gain_weight"
    BUILD_MUSCLE = "build_muscle"
    IMPROVE_HEALTH = "improve_health"
    REDUCE_SUGAR = "reduce_sugar"
    INCREASE_PROTEIN = "increase_protein"

@dataclass
class UserProfile:
    """Profil utilisateur pour personnaliser les scores YUmi"""

    # Informations de base
    name: str
    age_group: AgeGroup
    activity_level: ActivityLevel

    # Restrictions alimentaires et allergies
    dietary_restrictions: List[DietaryRestriction]
    allergies: List[str]  # Liste d'allergènes (ex: "nuts", "eggs", "milk")

    # Objectifs de santé
    health_goals: List[HealthGoal]

    # Budget alimentaire (en euros par semaine)
    weekly_budget: Optional[float] = 50.0  # Budget par défaut de 50€/semaine

    # Préférences personnelles
    alcohol_allowed: bool = False
    max_sugar_tolerance: Optional[float] = None  # g/100g
    max_sodium_tolerance: Optional[float] = None  # g/100g
    min_fiber_preference: Optional[float] = None  # g/100g
    min_protein_preference: Optional[float] = None  # g/100g

    # Facteurs de pondération personnalisés (-1.0 à 1.0)
    sugar_sensitivity: float = 0.0      # Plus élevé = plus restrictif sur le sucre
    sodium_sensitivity: float = 0.0     # Plus élevé = plus restrictif sur le sodium
    calorie_sensitivity: float = 0.0    # Plus élevé = plus restrictif sur les calories

    def __post_init__(self):
        """Validation et ajustements automatiques du profil"""

        # Ajustements automatiques selon l'âge
        if self.age_group == AgeGroup.CHILD:
            # Les enfants sont plus sensibles au sucre et sodium
            self.sugar_sensitivity = max(self.sugar_sensitivity, 0.3)
            self.sodium_sensitivity = max(self.sodium_sensitivity, 0.2)
            # Alcool strictement interdit pour les enfants
            self.alcohol_allowed = False

        elif self.age_group == AgeGroup.TEENAGER:
            # Adolescents : restriction alcool et attention au sucre
            self.alcohol_allowed = False
            self.sugar_sensitivity = max(self.sugar_sensitivity, 0.1)

        elif self.age_group == AgeGroup.SENIOR:
            # Seniors : plus sensibles au sodium et aux calories
            self.sodium_sensitivity = max(self.sodium_sensitivity, 0.2)
            self.calorie_sensitivity = max(self.calorie_sensitivity, 0.1)

        # Ajustements selon les objectifs de santé
        if HealthGoal.LOSE_WEIGHT in self.health_goals:
            self.calorie_sensitivity = max(self.calorie_sensitivity, 0.3)
            self.sugar_sensitivity = max(self.sugar_sensitivity, 0.2)

        if HealthGoal.REDUCE_SUGAR in self.health_goals:
            self.sugar_sensitivity = max(self.sugar_sensitivity, 0.5)

        if DietaryRestriction.DIABETIC in self.dietary_restrictions:
            self.sugar_sensitivity = max(self.sugar_sensitivity, 0.8)
            self.max_sugar_tolerance = min(self.max_sugar_tolerance or 5.0, 5.0)

        if DietaryRestriction.LOW_SODIUM in self.dietary_restrictions:
            self.sodium_sensitivity = max(self.sodium_sensitivity, 0.6)
            self.max_sodium_tolerance = min(self.max_sodium_tolerance or 0.3, 0.3)

    def get_alcohol_restriction_level(self) -> float:
        """Retourne le niveau de restriction sur l'alcool (0.0 = autorisé, 1.0 = interdit)"""
        if not self.alcohol_allowed:
            return 1.0

        # Même si autorisé, peut être restreint selon l'âge ou les objectifs
        restriction = 0.0

        if self.age_group in [AgeGroup.CHILD, AgeGroup.TEENAGER]:
            restriction = 1.0
        elif HealthGoal.IMPROVE_HEALTH in self.health_goals:
            restriction = 0.8
        elif HealthGoal.LOSE_WEIGHT in self.health_goals:
            restriction = 0.6

        return restriction

    def get_sugar_penalty_multiplier(self) -> float:
        """Retourne le multiplicateur de pénalité pour le sucre"""
        base_multiplier = 1.0
        return base_multiplier + self.sugar_sensitivity

    def get_sodium_penalty_multiplier(self) -> float:
        """Retourne le multiplicateur de pénalité pour le sodium"""
        base_multiplier = 1.0
        return base_multiplier + self.sodium_sensitivity

    def get_calorie_penalty_multiplier(self) -> float:
        """Retourne le multiplicateur de pénalité pour les calories"""
        base_multiplier = 1.0
        return base_multiplier + self.calorie_sensitivity

    def check_allergies(self, product_categories: List[str], product_ingredients: List[str] = None) -> List[str]:
        """Vérifie les allergies dans un produit et retourne la liste des allergènes détectés"""
        detected_allergens = []

        if not self.allergies:
            return detected_allergens

        # Vérifier dans les catégories
        for category in product_categories:
            for allergen in self.allergies:
                if allergen.lower() in category.lower():
                    detected_allergens.append(allergen)

        # Vérifier dans les ingrédients si disponibles
        if product_ingredients:
            for ingredient in product_ingredients:
                for allergen in self.allergies:
                    if allergen.lower() in ingredient.lower():
                        detected_allergens.append(allergen)

        return list(set(detected_allergens))  # Enlever les doublons

    def check_dietary_restrictions(self, product_categories: List[str], product_labels: List[str] = None, product_name: str = "") -> List[DietaryRestriction]:
        """Vérifie les restrictions alimentaires violées par un produit"""
        violations = []

        # Combiner toutes les sources d'information
        all_text_sources = product_categories + (product_labels or []) + [product_name]
        combined_text = ' '.join(all_text_sources).lower()

        for restriction in self.dietary_restrictions:
            if restriction == DietaryRestriction.VEGETARIAN:
                # Détection plus précise pour les produits carnés
                meat_keywords = ['meat', 'fish', 'seafood', 'poultry', 'chicken', 'beef', 'pork', 'lamb',
                               'turkey', 'duck', 'salmon', 'tuna', 'ham', 'bacon', 'sausage', 'charcuterie',
                               'jambon', 'saucisse', 'chorizo', 'salami', 'viande']
                if any(keyword in combined_text for keyword in meat_keywords):
                    violations.append(restriction)

            elif restriction == DietaryRestriction.VEGAN:
                # Détection étendue pour tous les produits d'origine animale
                animal_keywords = ['meat', 'fish', 'seafood', 'poultry', 'chicken', 'beef', 'pork', 'lamb',
                                 'turkey', 'duck', 'salmon', 'tuna', 'ham', 'bacon', 'sausage', 'charcuterie',
                                 'jambon', 'saucisse', 'chorizo', 'salami', 'viande',
                                 'dairy', 'milk', 'cheese', 'yogurt', 'butter', 'cream', 'eggs', 'honey',
                                 'lait', 'fromage', 'yaourt', 'beurre', 'crème', 'œuf', 'miel']
                if any(keyword in combined_text for keyword in animal_keywords):
                    violations.append(restriction)

            elif restriction == DietaryRestriction.GLUTEN_FREE:
                # Détection étendue pour le gluten
                gluten_keywords = ['wheat', 'gluten', 'bread', 'pasta', 'cereal', 'flour', 'barley', 'rye',
                                 'blé', 'farine', 'pain', 'pâtes', 'céréales', 'orge', 'seigle', 'avoine']
                if any(keyword in combined_text for keyword in gluten_keywords):
                    violations.append(restriction)

            elif restriction == DietaryRestriction.LACTOSE_FREE:
                # Détection étendue pour le lactose
                lactose_keywords = ['dairy', 'milk', 'cheese', 'yogurt', 'butter', 'cream', 'lactose',
                                  'lait', 'fromage', 'yaourt', 'beurre', 'crème', 'lactose']
                if any(keyword in combined_text for keyword in lactose_keywords):
                    violations.append(restriction)

            elif restriction == DietaryRestriction.HALAL:
                # Détection intelligente AMÉLIORÉE pour les produits halal

                # 1. Vérifier d'abord si c'est explicitement certifié halal
                halal_indicators = [
                    'halal', 'hallal', 'halaal', 'certified-halal', 'certifié-halal',
                    'halal-certified', 'muslim-friendly', 'islamique'
                ]
                is_explicitly_halal = any(indicator in combined_text for indicator in halal_indicators)

                if not is_explicitly_halal:
                    # 2. Détection spécifique des violations halal
                    pork_keywords = [
                        'pork', 'pig', 'ham', 'bacon', 'prosciutto',
                        'jambon', 'porc', 'cochon', 'lard', 'rillettes', 'boudin',
                        'pancetta'
                    ]

                    alcohol_keywords = [
                        'alcohol', 'wine', 'beer', 'spirits', 'liqueur', 'vodka', 'whisky', 'rum', 'gin',
                        'alcool', 'vin', 'bière', 'spiritueux', 'cognac', 'champagne'
                    ]

                    # Charcuteries spécifiquement de porc
                    pork_charcuterie_keywords = [
                        'chorizo', 'salami', 'saucisson', 'mortadelle'
                    ]

                    # Gélatine de porc
                    gelatin_keywords = ['gelatin', 'gélatine']

                    # Vérifier les violations
                    violating_keywords = pork_keywords + alcohol_keywords + pork_charcuterie_keywords + gelatin_keywords

                    if any(keyword in combined_text for keyword in violating_keywords):
                        violations.append(restriction)

                    # Cas spécial pour "charcuterie" générique - seulement si pas halal et contient des indices de porc
                    elif 'charcuterie' in combined_text:
                        # Rechercher des indices de porc dans le contexte
                        pork_context_keywords = ['porc', 'pork', 'cochon', 'pig']
                        if any(keyword in combined_text for keyword in pork_context_keywords):
                            violations.append(restriction)

        return violations

    def to_dict(self) -> dict:
        """Convertit le profil en dictionnaire"""
        return {
            'name': self.name,
            'age_group': self.age_group.value,
            'activity_level': self.activity_level.value,
            'dietary_restrictions': [dr.value for dr in self.dietary_restrictions],
            'allergies': self.allergies,
            'health_goals': [hg.value for hg in self.health_goals],
            'alcohol_allowed': self.alcohol_allowed,
            'max_sugar_tolerance': self.max_sugar_tolerance,
            'max_sodium_tolerance': self.max_sodium_tolerance,
            'min_fiber_preference': self.min_fiber_preference,
            'min_protein_preference': self.min_protein_preference,
            'sugar_sensitivity': self.sugar_sensitivity,
            'sodium_sensitivity': self.sodium_sensitivity,
            'calorie_sensitivity': self.calorie_sensitivity,
            'weekly_budget': self.weekly_budget
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'UserProfile':
        """Crée un profil à partir d'un dictionnaire"""
        return cls(
            name=data['name'],
            age_group=AgeGroup(data['age_group'].lower()),
            activity_level=ActivityLevel(data['activity_level'].lower()),
            dietary_restrictions=[DietaryRestriction(dr.lower()) for dr in data.get('dietary_restrictions', [])],
            allergies=data.get('allergies', []),
            health_goals=[HealthGoal(hg.lower()) for hg in data.get('health_goals', [])],
            alcohol_allowed=data.get('alcohol_allowed', False),
            max_sugar_tolerance=data.get('max_sugar_tolerance'),
            max_sodium_tolerance=data.get('max_sodium_tolerance'),
            min_fiber_preference=data.get('min_fiber_preference'),
            min_protein_preference=data.get('min_protein_preference'),
            sugar_sensitivity=data.get('sugar_sensitivity', 0.0),
            sodium_sensitivity=data.get('sodium_sensitivity', 0.0),
            calorie_sensitivity=data.get('calorie_sensitivity', 0.0),
            weekly_budget=data.get('weekly_budget', 50.0)
        )
# Profils prédéfinis pour différents types d'utilisateurs

def create_child_profile(name: str, allergies: List[str] = None) -> UserProfile:
    """Crée un profil pour enfant (3-12 ans)"""
    return UserProfile(
        name=name,
        age_group=AgeGroup.CHILD,
        activity_level=ActivityLevel.MODERATE,
        dietary_restrictions=[],
        allergies=allergies or [],
        health_goals=[HealthGoal.IMPROVE_HEALTH],
        alcohol_allowed=False,
        max_sugar_tolerance=15.0,
        max_sodium_tolerance=0.5
    )

def create_teenager_profile(name: str, health_goals: List[HealthGoal] = None) -> UserProfile:
    """Crée un profil pour adolescent (13-17 ans)"""
    return UserProfile(
        name=name,
        age_group=AgeGroup.TEENAGER,
        activity_level=ActivityLevel.ACTIVE,
        dietary_restrictions=[],
        allergies=[],
        health_goals=health_goals or [HealthGoal.MAINTAIN_WEIGHT],
        alcohol_allowed=False,
        max_sugar_tolerance=20.0
    )

def create_adult_profile(name: str, **kwargs) -> UserProfile:
    """Crée un profil pour adulte avec options personnalisables"""
    defaults = {
        'age_group': AgeGroup.ADULT,
        'activity_level': ActivityLevel.MODERATE,
        'dietary_restrictions': [],
        'allergies': [],
        'health_goals': [HealthGoal.MAINTAIN_WEIGHT],
        'alcohol_allowed': True
    }
    defaults.update(kwargs)

    return UserProfile(name=name, **defaults)

def create_senior_profile(name: str, health_conditions: List[str] = None) -> UserProfile:
    """Crée un profil pour senior (65+ ans)"""
    restrictions = []
    health_goals = [HealthGoal.IMPROVE_HEALTH]

    # Ajuster selon les conditions de santé
    if health_conditions:
        if 'diabetes' in health_conditions:
            restrictions.append(DietaryRestriction.DIABETIC)
            health_goals.append(HealthGoal.REDUCE_SUGAR)
        if 'hypertension' in health_conditions:
            restrictions.append(DietaryRestriction.LOW_SODIUM)

    return UserProfile(
        name=name,
        age_group=AgeGroup.SENIOR,
        activity_level=ActivityLevel.LIGHT,
        dietary_restrictions=restrictions,
        allergies=[],
        health_goals=health_goals,
        alcohol_allowed=False,
        max_sugar_tolerance=10.0,
        max_sodium_tolerance=0.3
    )
