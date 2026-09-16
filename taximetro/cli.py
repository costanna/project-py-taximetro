from taximetro.config import cargar_tarifas
from taximetro.core import ESTADO_MOVIMIENTO, ESTADO_PARADO, Taximetro
from taximetro.logger import get_logger
from taximetro.storage import AlmacenCarreras

logger = get_logger(__name__)

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


def ejecutar_carrera(taximetro, almacen):
    taximetro.iniciar_carrera()
    logger.info("Carrera iniciada.")
    print("\n🚕 Carrera iniciada. Estado inicial: PARADO.")

    while taximetro.en_curso:
        comando = pedir_comando()
        if comando == "m":
            if taximetro.cambiar_estado(ESTADO_MOVIMIENTO):
                logger.info("Cambio de estado -> movimiento")
                print(f"\n🔄 Estado cambiado a: {ESTADO_MOVIMIENTO.upper()}")
            else:
                print(f"\nYa estás en estado '{ESTADO_MOVIMIENTO.upper()}'.")
        elif comando == "p":
            if taximetro.cambiar_estado(ESTADO_PARADO):
                logger.info("Cambio de estado -> parado")
                print(f"\n🔄 Estado cambiado a: {ESTADO_PARADO.upper()}")
            else:
                print(f"\nYa estás en estado '{ESTADO_PARADO.upper()}'.")
        elif comando == "f":
            resumen = taximetro.finalizar_carrera()
            almacen.guardar_carrera(resumen)
            logger.info("Carrera finalizada: %.2f €", resumen["importe_total"])
            print(
                f"\n🏁 Carrera finalizada. Importe total a cobrar: {resumen['importe_total']:.2f} €"
            )


def main():
    tarifas = cargar_tarifas()
    taximetro = Taximetro(**tarifas)
    almacen = AlmacenCarreras()
    logger.info("Taxímetro arrancado. Tarifas: %s", tarifas)

    mostrar_instrucciones(taximetro)

    while True:
        respuesta = input("\n¿Iniciar nueva carrera? (s/n): ").strip().lower()
        if respuesta != "s":
            print("\n👋 Fin del turno. ¡Buen día!")
            logger.info("Fin del turno.")
            break
        ejecutar_carrera(taximetro, almacen)


if __name__ == "__main__":
    main()
