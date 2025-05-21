"""Python Sudoku Solver
https://github.com/pablosambuco/pysudoku
"""

# pylint: disable=redefined-builtin
import math
from itertools import combinations
from rich import print
from rich.table import Table

COLUMNA = "Columna"
FILA = "Fila"
CUADRO = "Cuadro"
LIMITE = 5
SIZE = 9  # el valor debe ser un cuadrado. 2^2, 3^2, 4^2...

VERBOSE = True

# TODO Desacoplar las llamadas al logger


def mensaje(celda, k, texto):
    """Funcion para imprimir mensajes por pantalla

    Args:
        celda (Celda): Celda en la que se realiza la accion a describir
        k (int/lint): Valor que se utiliza en la accion
        texto (string): Descripcion de la accion realizada
    """
    txt = "Nivel {:02n}. {} [red]{}[/red] = {}"
    num = Tablero.vuelta
    pos = celda.posicion()
    print(txt.format(num, texto, pos, k))


class Logger:
    """Logger"""

    def __init__(self, verbose=True):
        """
        Logger configurable para salida condicional.

        Args:
            verbose (bool): si False, no se imprime nada
        """
        self.verbose = verbose

    def print(self, *args, **kwargs):
        """
        Imprime mensaje si verbose está activo.

        Los argumentos y kwargs son compatibles con print()
        """
        if not self.verbose:
            return
        print(*args, **kwargs)


class Celda:
    """Cada casillero del tablero debe ser una instancia de esta clase"""

    def __init__(self):
        """Constructor de Celda"""
        self.valor = None
        self.posible = [x + 1 for x in range(SIZE)]
        self.grupos = {}
        self.original = False

    def vacia(self):
        """Metodo de verificacion de contenido de la celda

        Returns:
            bool: Indica si la celda esta vacia
        """
        return self.valor is None

    def setvalor(self, valor, original=False, logger=None):
        """Metodo para establecer el contenido de la celda

        Se intenta quitar el valor posible de las celdas de los grupos.
        Si una de ellas no lo permite, no se realiza la accion

        Args:
            valor (int): valor a ingresar a la celda

        Returns:
            bool: Resultado de la accion
        """
        if valor in self.posible:
            self.valor = valor
            self.posible = [valor]
            self.original = original
            if logger:
                logger.print(
                    f"Nivel {Tablero.vuelta:02n}. "
                    + f"Asignando {valor} a {self.posicion()}"
                )
            for _, v in self.grupos.items():
                v.quitar(self, valor, logger)
            return True
        return False

    def quitar(self, valor, logger=None):
        """Metodo para quitar un valor posible de la celda

        Se quita el valor del listado de posibles.
        Si solamente queda un valor posible, se aplica a la celda llamando a
        setvalor()

        Args:
            valor (int): valor a quitar de la lista de posibles

        Returns:
            bool: Resultado de la accion
        """
        if self.vacia() and valor in self.posible:
            self.posible.remove(valor)
            if logger:
                logger.print(
                    f"Nivel {Tablero.vuelta:02n}. "
                    + f"Quitando {valor} de {self.posicion()}"
                )
            if len(self.posible) == 1:
                if logger:
                    logger.print(
                        f"Nivel {Tablero.vuelta:02n}. Único valor "
                        + f"{self.posible[0]} en {self.posicion()}, asignando"
                    )
                return self.setvalor(self.posible[0], logger)
        return bool(self.posible)

    def agrupar(self, grupo):
        """Metodo para agrupar las celdas dentro de filas, columnas y cuadros

        Para cada tipo (grupo.tipo) se genera una clave en el
        diccionario self.grupos

        Args:
            grupo (Grupo): Grupo al que se asigna la celda
        """
        self.grupos[grupo.tipo] = grupo

    def incluye(self, lista):
        """Metodo para verificar si los posibles incluyen todos los elementos
        de una lista

        Args:
            lista (list): Lista cuyos elementos se buscaran

        Returns:
            bool: resultado de la comparacion
        """
        return set(lista).issubset(set(self.posible))

    def __str__(self):
        """Metodo de conversion a texto

        Returns:
            string: contenido o valores posibles de la celda
        """
        string = ""
        if self.vacia():
            string += "[red]"
            for valor in self.posible:
                string += str(valor)
            string += "[/red]"
        elif self.original:
            string += "[bright_cyan]" + str(self.valor) + "[/bright_cyan]"
        else:
            string += "[green]" + str(self.valor) + "[/green]"
        return string

    def posicion(self):
        """Metodo de lectura de posicion

        Returns:
            string: (fila, columna) en formato humano
        """
        fila = self.grupos[FILA].posicion
        columna = self.grupos[COLUMNA].posicion
        return f"({fila + 1},{columna + 1})"


class Grupo:
    """Cada fila, columna o cuadro del tablero"""

    def __init__(self, tipo, posicion):
        """Constructor del grupo

        Args:
            tipo (CONSTANTE): Constante de tipo
            posicion (int): posicion del grupo en el tablero (0..8)
        """
        self.tipo = tipo
        self.celdas = []
        self.posicion = posicion

    def __getitem__(self, pos):
        """Definicion del operador []

        Permite operar con los grupos como si se tratara de listas de celdas

        Args:
            pos (int): posicion de la celda a obtener dentro del grupo

        Returns:
            Celda: objeto celda de la posicion solicitada
        """
        return self.celdas[pos]

    def quitar(self, celda, valor, logger=None):
        """Metodo para quitar un valor posible del grupo

        Args:
            celda (Celda): celda que tendra el valor asignado
            valor (int): valor a quitar del resto de celdas del grupo
        """
        for caux in self.celdas:
            if caux != celda and caux.vacia():
                if not caux.quitar(valor, logger):
                    return False
        return True

    def agrupar(self, celda):
        """Metodo para agrupar celdas dentro de este grupo

        Se llama tambien al metodo agrupar() de la celda

        Args:
            celda (Celda): Celda que se asigna al grupo
        """
        celda.agrupar(self)
        self.celdas.append(celda)

    def row(self):
        """Metodo para conversion a texto

        Returns:
            list(string): lista de valores de las celdas del grupo
        """
        row = []
        for caux in self.celdas:
            row.append(str(caux))
        return row

    def verificar(self):
        """Metodo de control

        Revisa los distintos valores del grupo.
        Si quedan valores, no esta resuelto

        Returns:
            bool grupo resuelto
        """
        total = [x + 1 for x in range(SIZE)]
        for caux in self.celdas:
            if caux.vacia():
                return False
            if caux.valor in total:
                total.remove(caux.valor)
        if total:  # la lista no esta vacia
            return False
        return True

    def incluye(self, comb):
        """Metodo auxiliar para contar celdas que incluyen una combinacion

        Args:
            comb (list): lista de valores a verificar

        Returns:
            int: cantidad de celdas que incluyen la combinacion
        """
        cantidad = 0
        for celda in self.celdas:
            if celda.incluye(comb):
                cantidad += 1
        return cantidad

    def incluye_unit(self, comb):
        """Metodo auxiliar para contar celdas que incluyen elementos, pero no
        la lista completa

        Args:
            comb (list): lista de valores a verificar

        Returns:
            int: cantidad de celdas que incluyen la combinacion
        """
        cantidad = 0
        for celda in self.celdas:
            for elem in comb:
                # cuento las que incluyen elem pero no comb
                if celda.incluye([elem]) and not celda.incluye(comb):
                    cantidad += 1
        return cantidad

    def asignar(self, comb, logger=None):
        """Metodo auxiliar para asignar valores posibles a celdas

        Args:
            comb (list): lista de valores a asiganr al grupo

        Returns:
            int: cantidad de celdas que se cambiaron
        """
        cambios = 0

        total = [i + 1 for i in range(SIZE)]
        resto = [i for i in total if i not in comb]
        for celda in self.celdas:
            if celda.vacia():
                if celda.incluye(comb):
                    for valor in resto:
                        cambios += celda.quitar(valor, logger)

        return cambios

    def revisar(self, logger=None):
        """Metodo de revision del grupo

        Si un valor solo es posible en una celda, se asigna.
        Si un grupo de N valores solo es posible en N celdas, se marcan posibles

        Returns:
            int: cantidad de cambios aplicados en la llamada
        """
        cambios = 0
        # verifico valores posibles únicos en el grupo
        for celda1 in self.celdas:
            if celda1.vacia():
                for valor in celda1.posible:
                    cantidad = self.incluye([valor])
                    if cantidad == 1:
                        # mensaje(celda1,valor,"Asumiendo por " + self.tipo)
                        celda1.setvalor(valor, logger)
                        cambios += 1

        # verifico combinaciones de N valores que se repiten en N celdas
        for celda in self.celdas:
            # recorro las combinaciones de distintas longitudes a partir de 2
            for largo in range(1, len(celda.posible)):
                for comb in combinations(celda.posible, largo):
                    cantidad = self.incluye(comb)
                    # si la cantidad es exactamente la longitud
                    if cantidad == largo and largo == len(comb):
                        cantidad_unitaria = self.incluye_unit(comb)
                        # si no hay celdas que cumplan
                        if cantidad_unitaria == 0:
                            cambios += self.asignar(comb, logger)
        return cambios


class Tablero:
    """Tablero de Sudoku, compuesto por filas, columnas y cuadros"""

    vuelta = 0  # variable de control para la recursividad

    def __init__(self):
        """Constructor del tablero"""

        self.filas = [Grupo(FILA, i) for i in range(SIZE)]
        self.columnas = [Grupo(COLUMNA, i) for i in range(SIZE)]
        self.cuadros = [Grupo(CUADRO, i) for i in range(SIZE)]
        self.celdas = []

        aux = int(math.sqrt(SIZE))

        for i in range(SIZE):
            for j in range(SIZE):
                celda = Celda()
                self.celdas.append(celda)
                self.filas[i].agrupar(celda)
                self.columnas[j].agrupar(celda)
                self.cuadros[int(j / aux) + int(i / aux) * aux].agrupar(celda)

    def copiar(self):
        """Metodo para generar una copia del tablero actual

        Returns:
            Tablero: el nuevo objeto copia del actual
        """
        aux = Tablero()
        for i in range(SIZE * SIZE):
            aux.celdas[i].valor = self.celdas[i].valor
            aux.celdas[i].posible = self.celdas[i].posible.copy()
        return aux

    def __getitem__(self, pos):
        """Definicion del operador [] para lectura y escritura

        Permite operar con el tablero como si se tratara de listas de grupos

        Args:
            pos (int): posicion x de la celda a obtener, o numero de columna

        Returns:
            Grupo: objeto columna de la posicion solicitada
        """
        return self.columnas[pos]

    def revisar(self, logger=None):
        """Metodo de revision de filas/columnas/cuadros"""
        cambios_tot = 0
        for _ in range(LIMITE):
            cambios = 0
            for i in self.filas:
                cambios += i.revisar(logger)
            for i in self.columnas:
                cambios += i.revisar(logger)
            for i in self.cuadros:
                cambios += i.revisar(logger)
            if cambios == 0:
                break
            cambios_tot += cambios
        return cambios_tot

    def resolver(self, profundidad=0, logger=None):
        """Metodo de resolución recursivo"""
        if not self.valido():
            if logger:
                logger.print(
                    f"[dim]↪ Estado inválido en profundidad {profundidad}[/dim]"
                )
            return 0  # Estado inválido

        cambios = self.revisar(logger)
        if self.verificar():
            if logger:
                logger.print(
                    "[green]✔ Tablero resuelto en "
                    + f"profundidad {profundidad}[/green]"
                )
            return cambios  # Ya está resuelto

        # Heurística: elegir celda vacía con menor cantidad de opciones
        celda_index = None
        min_opciones = SIZE + 1
        for i, celda in enumerate(self.celdas):
            if celda.vacia() and 0 < len(celda.posible) < min_opciones:
                celda_index = i
                min_opciones = len(celda.posible)

        # if celda_index is None:
        #    return cambios  # No hay más celdas vacías

        celda = self.celdas[celda_index]
        for valor in celda.posible:
            copia = self.copiar()
            if logger:
                logger.print(
                    f"[blue]➤ Profundidad {profundidad}: "
                    + f"probando {valor} en {celda.posicion()}[/blue]"
                )
            if copia.celdas[celda_index].setvalor(valor, logger):
                Tablero.vuelta += 1
                resultado = copia.resolver(profundidad + 1, logger)
                Tablero.vuelta -= 1

                if copia.verificar():  # Se resolvió exitosamente
                    if logger:
                        logger.print(
                            "[green]✔ Solución encontrada en "
                            + f"{celda.posicion()} con valor {valor}[/green]"
                        )
                    self.replicar(copia)
                    return cambios + resultado
                else:
                    if logger:
                        logger.print(
                            "[yellow]↩ Retroceso desde "
                            + f"{celda.posicion()} con valor {valor}[/yellow]"
                        )

        return cambios  # Ninguna opción válida funcionó

    def cargar(self, tablero, logger=None):
        """Metodo de carga del tablero

        Args:
            tablero (list): lista de N listas de N enteros que forman el sudoku

        Returns:
            bool: estado de carga del tablero
        """
        for i in range(SIZE):
            for j in range(SIZE):
                if tablero[i][j] != 0:
                    if not self[j][i].setvalor(tablero[i][j], True, logger):
                        return False
        return True

    def replicar(self, tablero):
        """Metodo de carga del tablero desde otro tablero

        Args:
            tablero (Tablero): tablero con los valores que se copian
        """
        for i in range(SIZE * SIZE):
            self.celdas[i].valor = tablero.celdas[i].valor
            self.celdas[i].posible = tablero.celdas[i].posible.copy()

    def completo(self):
        """Metodo simple de control

        Returns:
            bool: tablero completo
        """
        for i in range(SIZE * SIZE):
            if self.celdas[i].vacia():
                return False
        return True

    def valido(self):
        """Metodo de control

        Valida que el tablero no tenga conflictos evidentes (duplicados o celdas sin posibilidades).

        Returns:
            bool: True si el tablero está en un estado válido parcial
        """
        # Valida que ninguna celda tenga conjunto vacío de posibles
        for celda in self.celdas:
            if celda.vacia() and not celda.posible:
                return False

        # Verifica que no haya duplicados en valores asignados por grupo
        for grupo in self.filas + self.columnas + self.cuadros:
            vistos = set()
            for celda in grupo.celdas:
                if not celda.vacia():
                    if celda.valor in vistos:
                        return False
                    vistos.add(celda.valor)
        return True

    def verificar(self):
        """Metodo de control

        Revisa los distintos grupos.
        Si algun grupo no esta resuelto, no esta resuelto el tablero

        Returns:
            bool tablero resuelto correctamente
        """
        for i in self.filas:
            if not i.verificar():
                return False
        for i in self.columnas:
            if not i.verificar():
                return False
        for i in self.cuadros:
            if not i.verificar():
                return False
        return True

    def table(self):
        """Metodo para conversion a texto

        Returns:
            rich.Table: tabla conteniendo el sudoku
        """
        table = Table(
            show_header=False,
            show_lines=True,
        )
        for col in range(SIZE):
            table.add_column(str(col), justify="center", width=SIZE * 2 + 3)
        for fila in self.filas:
            table.add_row(*fila.row())
        return table


def main():
    """main"""

    carga = [
        # trivial
        # [1, 2, 3, 4, 5, 6, 7, 8, 9],
        # [4, 5, 6, 7, 8, 9, 1, 2, 3],
        # [7, 8, 9, 1, 2, 3, 4, 5, 6],
        # [2, 3, 4, 5, 6, 7, 8, 9, 1],
        # [5, 6, 7, 8, 9, 1, 2, 3, 4],
        # [8, 9, 1, 2, 3, 4, 5, 6, 7],
        # [3, 4, 5, 6, 7, 8, 9, 1, 2],
        # [6, 7, 8, 9, 1, 2, 3, 4, 5],
        # [9, 1, 2, 3, 4, 5, 6, 7, 8],
        #
        # el sudoku mas dificil del mundo 9x9
        # [8, 0, 0, 0, 0, 0, 0, 0, 0],
        # [0, 0, 3, 6, 0, 0, 0, 0, 0],
        # [0, 7, 0, 0, 9, 0, 2, 0, 0],
        # [0, 5, 0, 0, 0, 7, 0, 0, 0],
        # [0, 0, 0, 0, 4, 5, 7, 0, 0],
        # [0, 0, 0, 1, 0, 0, 0, 3, 0],
        # [0, 0, 1, 0, 0, 0, 0, 6, 8],
        # [0, 0, 8, 5, 0, 0, 0, 1, 0],
        # [0, 9, 0, 0, 0, 0, 4, 0, 0],
        #
        # test 4x4
        # [1, 0, 0, 0],
        # [2, 0, 0, 0],
        # [3, 0, 0, 0],
        # [4, 0, 0, 0],
        #
        # vacio NxN
        # [0 for x in range(SIZE)] for y in range(SIZE)
        #
        # Basico: 4 vueltas
        # [0, 0, 0, 0, 5, 0, 0, 0, 9],
        # [0, 0, 0, 3, 0, 0, 8, 4, 0],
        # [4, 3, 0, 1, 8, 7, 0, 6, 0],
        # [3, 0, 8, 0, 0, 0, 0, 7, 0],
        # [0, 0, 0, 4, 3, 2, 0, 0, 0],
        # [0, 5, 0, 0, 0, 0, 9, 0, 2],
        # [0, 4, 0, 2, 1, 0, 0, 9, 8],
        # [0, 9, 3, 0, 0, 8, 0, 0, 0],
        # [7, 0, 0, 0, 9, 0, 0, 0, 0],
        #
        # Intermedio: 11 vueltas, con recursividad
        # [0, 4, 3, 0, 2, 0, 8, 0, 0],
        # [7, 9, 0, 0, 5, 4, 0, 0, 0],
        # [0, 0, 0, 0, 0, 0, 0, 0, 9],
        # [0, 0, 0, 6, 0, 0, 9, 0, 7],
        # [0, 0, 0, 5, 0, 8, 0, 0, 0],
        # [1, 0, 7, 0, 0, 2, 0, 0, 0],
        # [3, 0, 0, 0, 0, 0, 0, 0, 0],
        # [0, 0, 0, 4, 6, 0, 0, 9, 1],
        # [0, 0, 5, 0, 8, 0, 7, 2, 0],
        #
        # Avanzado: 10 vueltas, con recursividad
        # [1, 0, 0, 9, 4, 0, 3, 0, 0],
        # [0, 0, 0, 0, 0, 8, 1, 0, 6],
        # [9, 0, 0, 0, 0, 0, 0, 2, 0],
        # [0, 7, 0, 1, 0, 4, 0, 0, 9],
        # [6, 0, 4, 0, 9, 0, 7, 0, 1],
        # [3, 0, 0, 6, 0, 7, 0, 4, 0],
        # [0, 9, 0, 0, 0, 0, 0, 0, 4],
        # [2, 0, 1, 4, 0, 0, 0, 0, 0],
        # [0, 0, 3, 0, 7, 6, 0, 0, 8],
        #
        # Otros: 5 vueltas
        # [8, 0, 0, 0, 0, 4, 0, 0, 6],
        # [2, 0, 0, 0, 5, 0, 1, 0, 0],
        # [9, 0, 0, 7, 0, 0, 0, 3, 0],
        # [5, 0, 0, 0, 0, 0, 0, 0, 9],
        # [0, 0, 0, 4, 0, 2, 0, 0, 0],
        # [1, 0, 0, 0, 0, 0, 0, 0, 8],
        # [0, 8, 0, 0, 0, 6, 0, 0, 2],
        # [0, 0, 7, 0, 3, 0, 0, 0, 5],
        # [4, 0, 0, 9, 0, 0, 0, 0, 1],
        #
        # websudoku evil: 6 vueltas
        # [0, 9, 0, 0, 4, 6, 0, 0, 3],
        # [0, 8, 0, 0, 7, 0, 0, 0, 0],
        # [1, 0, 0, 0, 0, 0, 2, 0, 0],
        # [0, 0, 1, 0, 0, 7, 0, 0, 5],
        # [0, 0, 3, 0, 2, 0, 6, 0, 0],
        # [7, 0, 0, 9, 0, 0, 1, 0, 0],
        # [0, 0, 9, 0, 0, 0, 0, 0, 4],
        # [0, 0, 0, 0, 3, 0, 0, 2, 0],
        # [2, 0, 0, 5, 8, 0, 0, 7, 0],
        #
        # scargot: 42 vueltas, con recursividad
        # [1, 0, 0, 0, 0, 7, 0, 9, 0],
        # [0, 3, 0, 0, 2, 0, 0, 0, 8],
        # [0, 0, 9, 6, 0, 0, 5, 0, 0],
        # [0, 0, 5, 3, 0, 0, 9, 0, 0],
        # [0, 1, 0, 0, 8, 0, 0, 0, 2],
        # [6, 0, 0, 0, 0, 4, 0, 0, 0],
        # [3, 0, 0, 0, 0, 0, 0, 1, 0],
        # [0, 4, 0, 0, 0, 0, 0, 0, 7],
        # [0, 0, 7, 0, 0, 0, 3, 0, 0],
        #
        # ejemplo web: 8 vueltas
        # [0, 0, 0, 0, 0, 0, 2, 0, 0],
        # [0, 5, 8, 0, 0, 6, 0, 0, 0],
        # [0, 0, 0, 3, 0, 0, 0, 8, 5],
        # [0, 1, 0, 4, 7, 0, 6, 0, 0],
        # [9, 0, 6, 0, 0, 0, 5, 0, 7],
        # [0, 0, 7, 0, 3, 9, 0, 4, 0],
        # [7, 6, 0, 0, 0, 8, 0, 0, 0],
        # [0, 0, 0, 9, 0, 0, 8, 1, 0],
        # [0, 0, 9, 0, 0, 0, 0, 0, 0],
        #
        # Imposible:
        # [0, 0, 0, 4, 0, 3, 8, 0, 0],
        # [5, 0, 0, 0, 9, 0, 0, 0, 0],
        # [0, 8, 6, 0, 0, 0, 0, 0, 7],
        # [0, 0, 5, 2, 0, 0, 0, 8, 4],
        # [0, 2, 1, 0, 0, 0, 0, 5, 0],
        # [0, 0, 0, 0, 0, 0, 7, 0, 9],
        # [1, 5, 0, 7, 0, 0, 9, 0, 8],
        # [4, 9, 0, 0, 1, 0, 2, 0, 0],
        # [0, 0, 0, 0, 0, 0, 0, 7, 1],
        #
        # Prueba:
        [8, 4, 0, 0, 0, 7, 3, 0, 1],
        [0, 0, 0, 0, 5, 0, 0, 8, 0],
        [0, 0, 9, 0, 3, 0, 7, 0, 0],
        [0, 0, 6, 0, 0, 3, 0, 0, 4],
        [4, 0, 0, 7, 0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0, 8, 0, 0, 3],
        [0, 0, 7, 0, 1, 0, 4, 0, 0],
        [0, 0, 0, 0, 8, 0, 0, 2, 0],
        [1, 6, 0, 0, 0, 2, 5, 0, 8],
    ]

    logger = Logger(verbose=VERBOSE)

    logger.print(carga)
    tab = Tablero()
    if tab.cargar(carga, logger=logger):
        logger.print(tab.table())
        cambios = tab.resolver(logger=logger)
        logger.print("Completo:", tab.completo())
        logger.print("Verificar:", tab.verificar())
        logger.print("Cambios:", cambios)
        logger.print(tab.table())
    else:
        logger.print("[red]Sudoku mal armado[/red]")


if __name__ == "__main__":
    main()
