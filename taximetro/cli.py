from taximetro.core import ESTADO_MOVIMIENTO, ESTADO_PARADO, Taximetro

COMANDOS_VALIDOS = {"m", "p", "f"}


def mostrar_instrucciones(taximetro):
    print("=" * 52)
    print("🚕  TAXÍMETRO DIGITAL — TaxiTech Solutions")
    print("=" * 52)
    print("Tarifas vigentes:")
    print(f"  · Parado o < 20 km/h : {taximetro.tarifa_parado:.2f} €/segundo")
    print(f"  · En movimiento      : {taximetro.tarifa_movimiento:.2f} €/segundo")
    print()
    print("Comandos disponibles durante una carrera:")
    print("  m -> cambiar a EN MOVIMIENTO")
    print("  p -> cambiar a PARADO")
    print("  f -> FINALIZAR la carrera y ver el importe total")
    print("=" * 52)


def pedir_comando():
    comando = input("\nComando (m/p/f): ").strip().lower()
    while comando not in COMANDOS_VALIDOS:
        print("⚠️  Comando no válido. Usa 'm', 'p' o 'f'.")
        comando = input("Comando (m/p/f): ").strip().lower()
    return comando


def ejecutar_carrera(taximetro):
    taximetro.iniciar_carrera()
    print("\n🚕 Carrera iniciada. Estado inicial: PARADO.")

    while taximetro.en_curso:
        comando = pedir_comando()
        if comando == "m":
            if taximetro.cambiar_estado(ESTADO_MOVIMIENTO):
                print(f"\n🔄 Estado cambiado a: {ESTADO_MOVIMIENTO.upper()}")
            else:
                print(f"\nYa estás en estado '{ESTADO_MOVIMIENTO.upper()}'.")
        elif comando == "p":
            if taximetro.cambiar_estado(ESTADO_PARADO):
                print(f"\n🔄 Estado cambiado a: {ESTADO_PARADO.upper()}")
            else:
                print(f"\nYa estás en estado '{ESTADO_PARADO.upper()}'.")
        elif comando == "f":
            resumen = taximetro.finalizar_carrera()
            print(
                f"\n🏁 Carrera finalizada. Importe total a cobrar: {resumen['importe_total']:.2f} €"
            )


def main():
    taximetro = Taximetro()
    mostrar_instrucciones(taximetro)

    while True:
        respuesta = input("\n¿Iniciar nueva carrera? (s/n): ").strip().lower()
        if respuesta != "s":
            print("\n👋 Fin del turno. ¡Buen día!")
            break
        ejecutar_carrera(taximetro)


if __name__ == "__main__":
    main()
