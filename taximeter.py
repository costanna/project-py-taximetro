"""
Taxímetro Digital — TaxiTech Solutions
Fase 1 — MVP Funcional (US-01 a US-04)

CLI que permite a un taxista iniciar una carrera, alternar entre estado
"parado" y "en movimiento", y finalizar la carrera para obtener el importe
total a cobrar. El importe se acumula de forma continua en función del
tiempo real transcurrido en cada estado.

Tarifas vigentes (Zona EMT Madrid, junio 2025):
  - Parado o velocidad < 20 km/h: 0.02 €/segundo
  - En movimiento:                0.05 €/segundo
"""

from taximetro.cli import main

if __name__ == "__main__":
    main()
