import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import './App.css'
import Scanner from './components/Scanner'
import Cart from './components/Cart'
import Profile from './components/Profile'
import Home from './components/Home'
import Recommendations from './components/Recommendations'
import History from './components/History'

function App() {
  const [userId] = useState('default') // En production, gérer l'authentification

  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-orange-100 via-pink-100 to-blue-100">
        <Routes>
          <Route path="/" element={<Home userId={userId} />} />
          <Route path="/scanner" element={<Scanner userId={userId} />} />
          <Route path="/cart" element={<Cart userId={userId} />} />
          <Route path="/profile" element={<Profile userId={userId} />} />
          <Route path="/recommendations" element={<Recommendations userId={userId} />} />
          <Route path="/history" element={<History userId={userId} />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
