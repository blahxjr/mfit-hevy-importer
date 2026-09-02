import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Container, Navbar, Nav } from 'react-bootstrap';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Navbar bg="dark" variant="dark" expand="lg">
          <Container>
            <Navbar.Brand href="/">MFIT → Hevy Orchestrator</Navbar.Brand>
            <Navbar.Toggle aria-controls="basic-navbar-nav" />
            <Navbar.Collapse id="basic-navbar-nav">
              <Nav className="ms-auto">
                <Nav.Link href="/">Home</Nav.Link>
                <Nav.Link href="/imports">Importações</Nav.Link>
              </Nav>
            </Navbar.Collapse>
          </Container>
        </Navbar>

        <Container className="mt-4">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/imports" element={<Imports />} />
          </Routes>
        </Container>
      </div>
    </Router>
  );
}

function Home() {
  return (
    <div>
      <h1>MFIT → Hevy Orchestrator</h1>
      <p>Sistema seguro para importar fichas de treino do MFIT para o Hevy</p>
      <p>
        <a href="/imports" className="btn btn-primary">
          Começar Importação
        </a>
      </p>
    </div>
  );
}

function Imports() {
  return (
    <div>
      <h2>Importações</h2>
      <p>Página de importações - a ser implementada</p>
    </div>
  );
}

export default App;
