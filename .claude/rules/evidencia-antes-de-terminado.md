# Evidencia antes de decir «terminado»

Adaptado de la regla de verificación de obra/superpowers (licencia MIT), resumida y traducida.

Antes de decir que algo está terminado, arreglado o que «pasa», hay que poder enseñar la prueba
de esta misma sesión y de este mismo estado del código:

1. Decide qué comando demuestra lo que vas a afirmar (tests, build, lint, la petición real).
2. Ejecútalo entero, ahora, después del último cambio.
3. Lee la salida completa: código de salida, recuento de fallos, avisos.
4. Afirma solo lo que esa salida respalda, y cítala (comando y recuento).

No valen como prueba: «debería funcionar», una ejecución de antes del último cambio, un test
parcial presentado como total, el informe de un subagente sin la salida que lo respalda, ni
compilar sin ejecutar.

| Afirmación | Prueba necesaria | No basta |
|---|---|---|
| Los tests pasan | La salida del comando con 0 fallos | Una ejecución anterior |
| El build funciona | Build con código 0 | Que el lint pase |
| El bug está arreglado | El síntoma original reproducido y ya sin fallo | Que el código cambió |
| El requisito está cumplido | Repaso punto por punto del requisito | Que los tests pasan |

Si no se ha podido verificar algo, se dice así, con el motivo.

Excepción para no repetir trabajo: si el hook Stop del repo o el subagente test-runner ya
mostraron la salida con este mismo diff, cítala en vez de volver a ejecutar la suite.
