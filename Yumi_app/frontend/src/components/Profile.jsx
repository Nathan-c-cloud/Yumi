import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import { Checkbox } from '@/components/ui/checkbox.jsx'
import { ArrowLeft, Save } from 'lucide-react'
import yumiLogo from '../assets/yumi_logo.png'

function Profile({ userId }) {
  const [profile, setProfile] = useState({
    name: '',
    age_group: 'adult',
    activity_level: 'moderate',
    dietary_restrictions: [],
    allergies: [],
    health_goals: [],
    alcohol_allowed: false,
    max_sugar_tolerance: null,
    max_sodium_tolerance: null
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  const ageGroups = [
    { value: 'child', label: 'Enfant (3-12 ans)' },
    { value: 'teenager', label: 'Adolescent (13-17 ans)' },
    { value: 'adult', label: 'Adulte (18-64 ans)' },
    { value: 'senior', label: 'Senior (65+ ans)' }
  ]

  const activityLevels = [
    { value: 'sedentary', label: 'Sédentaire' },
    { value: 'light', label: 'Activité légère' },
    { value: 'moderate', label: 'Activité modérée' },
    { value: 'active', label: 'Actif' },
    { value: 'very_active', label: 'Très actif' }
  ]

  const dietaryRestrictions = [
    { value: 'vegetarian', label: 'Végétarien' },
    { value: 'vegan', label: 'Vegan' },
    { value: 'gluten_free', label: 'Sans gluten' },
    { value: 'lactose_free', label: 'Sans lactose' },
    { value: 'halal', label: 'Halal' },
    { value: 'kosher', label: 'Casher' },
    { value: 'low_sodium', label: 'Faible en sodium' },
    { value: 'diabetic', label: 'Diabétique' }
  ]

  const healthGoals = [
    { value: 'maintain_weight', label: 'Maintenir le poids' },
    { value: 'lose_weight', label: 'Perdre du poids' },
    { value: 'gain_weight', label: 'Prendre du poids' },
    { value: 'build_muscle', label: 'Développer les muscles' },
    { value: 'improve_health', label: 'Améliorer la santé' },
    { value: 'reduce_sugar', label: 'Réduire le sucre' },
    { value: 'increase_protein', label: 'Augmenter les protéines' }
  ]

  useEffect(() => {
    fetchProfile()
  }, [])

  const fetchProfile = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5002/api/profile', {
        headers: {
          'X-User-ID': userId
        }
      } )

      if (response.ok) {
        const data = await response.json()
        if (data.success && data.profile) {
          setProfile(data.profile)
        }
        // If profile is null, keep the default values already set in useState
      }
    } catch (err) {
      console.error('Erreur lors du chargement du profil')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setMessage('')

    try {
      const response = await fetch('http://127.0.0.1:5002/api/profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId
        },
        body: JSON.stringify(profile )
      })

      if (response.ok) {
        setMessage('Profil enregistré avec succès !')
      } else {
        setMessage('Erreur lors de l\'enregistrement du profil')
      }
    } catch (err) {
      setMessage('Erreur de connexion au serveur')
    } finally {
      setSaving(false)
    }
  }

  const toggleRestriction = (restriction) => {
    setProfile(prev => ({
      ...prev,
      dietary_restrictions: prev.dietary_restrictions.includes(restriction)
        ? prev.dietary_restrictions.filter(r => r !== restriction)
        : [...prev.dietary_restrictions, restriction]
    }))
  }

  const toggleGoal = (goal) => {
    setProfile(prev => ({
      ...prev,
      health_goals: prev.health_goals.includes(goal)
        ? prev.health_goals.filter(g => g !== goal)
        : [...prev.health_goals, goal]
    }))
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-xl">Chargement du profil...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen p-4">
      <div className="container mx-auto max-w-2xl">
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-2xl p-8">
          <div className="flex items-center justify-between mb-6">
            <Link to="/">
              <Button variant="ghost" className="flex items-center gap-2">
                <ArrowLeft className="h-5 w-5" />
                Retour
              </Button>
            </Link>
            <img src={yumiLogo} alt="Yumi" className="h-12" />
          </div>

          <h2 className="text-3xl font-bold mb-6 bg-gradient-to-r from-orange-500 via-pink-500 to-blue-500 bg-clip-text text-transparent">
            Mon Profil
          </h2>

          {message && (
            <div className={`px-4 py-3 rounded mb-4 ${message.includes('succès') ? 'bg-green-100 border border-green-400 text-green-700' : 'bg-red-100 border border-red-400 text-red-700'}`}>
              {message}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <Label htmlFor="name">Nom</Label>
              <Input
                id="name"
                value={profile.name}
                onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                placeholder="Votre nom"
                className="mt-1"
              />
            </div>

            <div>
              <Label htmlFor="age_group">Groupe d'âge</Label>
              <Select value={profile.age_group} onValueChange={(value) => setProfile({ ...profile, age_group: value })}>
                <SelectTrigger className="mt-1">
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
              <Label htmlFor="activity_level">Niveau d'activité</Label>
              <Select value={profile.activity_level} onValueChange={(value) => setProfile({ ...profile, activity_level: value })}>
                <SelectTrigger className="mt-1">
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
              <Label>Restrictions alimentaires</Label>
              <div className="grid grid-cols-2 gap-2 mt-2">
                {dietaryRestrictions.map(restriction => (
                  <div key={restriction.value} className="flex items-center space-x-2">
                    <Checkbox
                      id={restriction.value}
                      checked={profile.dietary_restrictions.includes(restriction.value)}
                      onCheckedChange={() => toggleRestriction(restriction.value)}
                    />
                    <label htmlFor={restriction.value} className="text-sm cursor-pointer">
                      {restriction.label}
                    </label>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <Label>Objectifs de santé</Label>
              <div className="grid grid-cols-2 gap-2 mt-2">
                {healthGoals.map(goal => (
                  <div key={goal.value} className="flex items-center space-x-2">
                    <Checkbox
                      id={goal.value}
                      checked={profile.health_goals.includes(goal.value)}
                      onCheckedChange={() => toggleGoal(goal.value)}
                    />
                    <label htmlFor={goal.value} className="text-sm cursor-pointer">
                      {goal.label}
                    </label>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="alcohol_allowed"
                checked={profile.alcohol_allowed}
                onCheckedChange={(checked) => setProfile({ ...profile, alcohol_allowed: checked })}
              />
              <label htmlFor="alcohol_allowed" className="cursor-pointer">
                Autoriser l'alcool
              </label>
            </div>

            <Button type="submit" className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-orange-500 via-pink-500 to-blue-500" disabled={saving}>
              <Save className="h-5 w-5" />
              {saving ? 'Enregistrement...' : 'Enregistrer le profil'}
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}

export default Profile
