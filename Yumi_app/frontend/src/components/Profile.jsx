import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, User, Save, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { API_ENDPOINTS } from '../config/api';
import yumiLogo from '../assets/yumi_logo.png';

function Profile({ userId }) {
  const [name, setName] = useState('');
  const [ageGroup, setAgeGroup] = useState('adult');
  const [activityLevel, setActivityLevel] = useState('moderate');
  const [dietaryRestrictions, setDietaryRestrictions] = useState([]);
  const [healthGoals, setHealthGoals] = useState([]);
  const [alcoholAllowed, setAlcoholAllowed] = useState(false);
  const [maxSugarTolerance, setMaxSugarTolerance] = useState('');
  const [maxSodiumTolerance, setMaxSodiumTolerance] = useState('');
  const [weeklyBudget, setWeeklyBudget] = useState(50); // Nouveau champ budget
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const ageGroups = [
    { value: 'child', label: 'Enfant (3-12 ans)' },
    { value: 'teenager', label: 'Adolescent (13-17 ans)' },
    { value: 'adult', label: 'Adulte (18-64 ans)' },
    { value: 'senior', label: 'Senior (65+ ans)' }
  ];

  const activityLevels = [
    { value: 'sedentary', label: 'Sédentaire' },
    { value: 'light', label: 'Activité légère' },
    { value: 'moderate', label: 'Activité modérée' },
    { value: 'active', label: 'Actif' },
    { value: 'very_active', label: 'Très actif' }
  ];

  const dietaryOptions = [
    { value: 'vegetarian', label: 'Végétarien' },
    { value: 'vegan', label: 'Vegan' },
    { value: 'gluten_free', label: 'Sans gluten' },
    { value: 'lactose_free', label: 'Sans lactose' },
    { value: 'halal', label: 'Halal' },
    { value: 'kosher', label: 'Casher' },
    { value: 'low_sodium', label: 'Faible en sodium' },
    { value: 'diabetic', label: 'Diabétique' }
  ];

  const healthGoalOptions = [
    { value: 'maintain_weight', label: 'Maintenir le poids' },
    { value: 'lose_weight', label: 'Perdre du poids' },
    { value: 'gain_weight', label: 'Prendre du poids' },
    { value: 'build_muscle', label: 'Développer les muscles' },
    { value: 'improve_health', label: 'Améliorer la santé' },
    { value: 'reduce_sugar', label: 'Réduire le sucre' },
    { value: 'increase_protein', label: 'Augmenter les protéines' }
  ];

  // Charger le profil au montage
  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(API_ENDPOINTS.PROFILE, {
        headers: {
          'X-User-ID': userId
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success && data.profile) {
          const { name, age_group, activity_level, dietary_restrictions, health_goals, alcohol_allowed, weekly_budget } = data.profile;
          setName(name);
          setAgeGroup(age_group);
          setActivityLevel(activity_level);
          setDietaryRestrictions(dietary_restrictions);
          setHealthGoals(health_goals);
          setAlcoholAllowed(alcohol_allowed);
          setWeeklyBudget(weekly_budget); // Charger le budget hebdomadaire
        }
      } else {
        setError('Erreur lors du chargement du profil');
      }
    } catch (err) {
      setError('Erreur de connexion au serveur');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    saveProfile();
  };

  const saveProfile = async () => {
    setIsLoading(true);
    setError('');
    setSuccessMessage('');

    try {
      const response = await fetch(API_ENDPOINTS.PROFILE, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId
        },
        body: JSON.stringify({
          name,
          age_group: ageGroup,
          activity_level: activityLevel,
          dietary_restrictions: dietaryRestrictions,
          health_goals: healthGoals,
          alcohol_allowed: alcoholAllowed,
          weekly_budget: weeklyBudget // Envoyer le budget hebdomadaire
        }),
      });

      if (response.ok) {
        setSuccessMessage('Profil enregistré avec succès !');
      } else {
        setError('Erreur lors de l\'enregistrement du profil');
      }
    } catch (err) {
      setError('Erreur de connexion au serveur');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleRestriction = (restriction) => {
    setDietaryRestrictions(prev =>
      prev.includes(restriction)
        ? prev.filter(r => r !== restriction)
        : [...prev, restriction]
    );
  };

  const toggleGoal = (goal) => {
    setHealthGoals(prev =>
      prev.includes(goal)
        ? prev.filter(g => g !== goal)
        : [...prev, goal]
    );
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="animate-spin h-8 w-8 text-gray-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-100 via-pink-100 to-blue-100">
      {/* Header */}
      <div className="w-full bg-white/80 backdrop-blur-sm shadow-sm p-4">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <Link to="/">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-5 w-5" />
            </Button>
          </Link>
          <img src={yumiLogo} alt="Yumi Logo" className="h-8" />
          <div className="w-10"></div> {/* Spacer for centering logo */}
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto p-6">
        <h2 className="text-4xl font-bold text-center mb-8" style={{ color: '#FF7043' }}>
          Mon Profil
        </h2>

        {error && (
          <div className="px-6 py-4 rounded-xl mb-6 font-medium text-center max-w-2xl mx-auto bg-red-100 border border-red-400 text-red-700">
            {error}
          </div>
        )}

        {successMessage && (
          <div className="px-6 py-4 rounded-xl mb-6 font-medium text-center max-w-2xl mx-auto bg-green-100 border border-green-400 text-green-700">
            {successMessage}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Informations personnelles */}
            <div className="bg-white rounded-xl shadow-xl p-6">
              <h3 className="text-2xl font-semibold mb-6 text-gray-800 border-b pb-3">
                📋 Informations personnelles
              </h3>

              <div className="space-y-6">
                <div>
                  <Label htmlFor="name" className="text-lg font-medium">Nom</Label>
                  <Input
                    id="name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Votre nom"
                    className="mt-2 text-lg p-3"
                  />
                </div>

                <div>
                  <Label htmlFor="age_group" className="text-lg font-medium">Groupe d'âge</Label>
                  <Select value={ageGroup} onValueChange={setAgeGroup}>
                    <SelectTrigger className="mt-2 text-lg p-3">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {ageGroups.map(group => (
                        <SelectItem key={group.value} value={group.value}>{group.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="activity_level" className="text-lg font-medium">Niveau d'activité</Label>
                  <Select value={activityLevel} onValueChange={setActivityLevel}>
                    <SelectTrigger className="mt-2 text-lg p-3">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {activityLevels.map(level => (
                        <SelectItem key={level.value} value={level.value}>{level.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="weekly_budget" className="text-lg font-medium">Budget hebdomadaire (€)</Label>
                  <Input
                    id="weekly_budget"
                    type="number"
                    value={weeklyBudget}
                    onChange={(e) => setWeeklyBudget(e.target.value)}
                    placeholder="Votre budget hebdomadaire"
                    className="mt-2 text-lg p-3"
                    min="0"
                  />
                </div>

                <div className="flex items-center space-x-3 p-4 bg-gray-50 rounded-lg">
                  <Checkbox
                    id="alcohol_allowed"
                    checked={alcoholAllowed}
                    onCheckedChange={setAlcoholAllowed}
                  />
                  <label htmlFor="alcohol_allowed" className="cursor-pointer text-lg font-medium">
                    Autoriser l'alcool
                  </label>
                </div>
              </div>
            </div>

            {/* Préférences alimentaires et santé */}
            <div className="bg-white rounded-xl shadow-xl p-6">
              <h3 className="text-2xl font-semibold mb-6 text-gray-800 border-b pb-3">
                🥗 Préférences et objectifs
              </h3>

              <div className="space-y-6">
                <div>
                  <Label className="text-lg font-medium">Restrictions alimentaires</Label>
                  <div className="grid grid-cols-1 gap-3 mt-3">
                    {dietaryOptions.map(option => (
                      <div key={option.value} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                        <Checkbox
                          id={option.value}
                          checked={dietaryRestrictions.includes(option.value)}
                          onCheckedChange={() => toggleRestriction(option.value)}
                        />
                        <label htmlFor={option.value} className="cursor-pointer font-medium flex-grow">
                          {option.label}
                        </label>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <Label className="text-lg font-medium">Objectifs de santé</Label>
                  <div className="grid grid-cols-1 gap-3 mt-3">
                    {healthGoalOptions.map(option => (
                      <div key={option.value} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                        <Checkbox
                          id={option.value}
                          checked={healthGoals.includes(option.value)}
                          onCheckedChange={() => toggleGoal(option.value)}
                        />
                        <label htmlFor={option.value} className="cursor-pointer font-medium flex-grow">
                          {option.label}
                        </label>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Bouton de sauvegarde */}
          <div className="mt-8 flex justify-center">
            <Button
              type="submit"
              className="px-12 py-4 text-lg font-bold bg-gradient-to-r from-orange-400 to-pink-500 text-white rounded-xl shadow-lg hover:shadow-xl transition-all transform hover:scale-105"
              disabled={isLoading}
            >
              <Save className="h-6 w-6 mr-2" />
              {isLoading ? 'Enregistrement...' : 'Enregistrer le profil'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default Profile;
