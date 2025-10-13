import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import gower
import warnings
import gc
import math

from gtda.homology import VietorisRipsPersistence
from gtda.metaestimators import CollectionTransformer
from gtda.time_series import TakensEmbedding
from gtda.diagrams import Scaler, PairwiseDistance
from gtda.pipeline import Pipeline

from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler


class TDA_similarity:
    def __init__(self,serie_cols: list,
                embedding_dimension:int = 100,
                embedding_time_delay:int = 10,
                stride:int =2,
                n_components:float=3,
                homology_dimensions:list = [0, 1],
                metric:str = "wasserstein",
                weights:list = None,
                method:str = 'average',
                scaler=MinMaxScaler()):
        """
        Clase principal para calcular índices de similitud híbridos entre municipios
        usando (1) características topológicas de series temporales (TDA) y (2)
        características tabulares (distancia de Gower).

        Parámetros principales:
            serie_cols (list): nombres de las columnas que contienen la serie temporal
                en los DataFrames de entrada (por ejemplo: ['t0','t1',...,'tN']).
            embedding_dimension (int): dimensión del embedding de Takens (m).
            embedding_time_delay (int): retardo (tau) para el embedding de Takens.
            stride (int): paso entre vectores de embedding.
            n_components (int): componentes principales por colección en PCA.
            homology_dimensions (list): dimensiones homológicas a calcular (ej. [0,1]).
            metric (str): métrica usada por PairwiseDistance ('wasserstein', 'bottleneck', ...).
            weights (list|None): pesos que combinan la matriz TDA y Gower (u otras matrices).
                Si se pasa None, se usarán pesos uniformes en el método weighted_similarity
                (pero la normalización se hace en weighted_similarity).
            method (str): 'average' (1 - distancia) o 'rbf' (aplica RBF sobre la distancia combinada).
            scaler: instancia de scaler para normalización (por defecto MinMaxScaler()).

        Notas:
            - La pipeline topológica se construye en build_topological_distance_pipeline().
            - Los parámetros no se validan exhaustivamente aquí; funciones internas
              lanzarán errores si la configuración es inconsistente (por ejemplo, embedding
              demasiado grande respecto al largo de las series).
        """
        self.weights = self.check_weights(weights)
        self.embedding_dimension = embedding_dimension
        self.embedding_time_delay = embedding_time_delay
        self.stride = stride
        self.metric = metric
        self.serie_cols= serie_cols
        self.n_components = n_components
        self.scaler = scaler
        self.method = method
        self.homology_dimensions = homology_dimensions
        self.pipeline = self.build_topological_distance_pipeline()

    def check_weights(self, weights:list):
        """
        Valida y devuelve la lista de pesos si corresponde.

        Args:
            weights (list|None): lista de floats cuya suma idealmente es 1.0.

        Returns:
            list|None: devuelve la misma lista si es válida, o None si se pasó None.

        Raises:
            ValueError: si se pasa una lista cuyos elementos no suman (aprox.) 1.0.

        Nota:
            - Para evitar problemas por errores numéricos flotantes, aquí podríamos
              aplicar una tolerancia o normalizar la lista. Por simplicidad devolvemos
              error si la suma difiere de 1 exactamente; la validación más fina se
              puede añadir si se desea.
        """
        if weights is not None and not math.isclose(sum(weights), 1.0, rel_tol=1e-9):
            raise ValueError("La suma de los pesos no es igual a 1")
        else:
            return weights

    def build_topological_distance_pipeline(self):
        """
        Construye y devuelve el pipeline topológico que transforma una colección de
        series temporales hasta obtener diagramas de persistencia escalados.

        El pipeline contiene los pasos:
            1) TakensEmbedding: reconstrucción del atractor.
            2) CollectionTransformer(PCA): reducción de dimensionalidad por colección.
            3) VietorisRipsPersistence: cálculo de los diagramas de persistencia.
            4) Scaler: escalado de diagramas para estabilidad numérica.

        Devuelve:
            Pipeline: objeto pipeline listo para fit_transform sobre una colección de series.
        """
        self.check_embedding_size()
        # Paso 1: Embedding (reconstrucción del atractor)
        embedder = TakensEmbedding(
            time_delay=self.embedding_time_delay,
            dimension=self.embedding_dimension,
            stride=self.stride
        )

        # Paso 2: Reducción PCA por colección (CollectionTransformer aplica PCA por cada serie/colección)
        batch_pca = CollectionTransformer(PCA(n_components=self.n_components), n_jobs=-1)

        # Paso 3: Cálculo de los diagramas de persistencia
        persistence = VietorisRipsPersistence(
            homology_dimensions=self.homology_dimensions, n_jobs=-1
        )

        # Paso 4: Escalado de los diagramas (normalización interna de las features topológicas)
        scaling = Scaler()

        # Pipeline completo → entrada: colección de series / salida: estructuras de persistencia escaladas
        topo_pipeline = Pipeline([
            ("embedder", embedder),
            ("pca", batch_pca),
            ("persistence", persistence),
            ("scaling", scaling)
            ])

        return topo_pipeline

    def check_embedding_size(self) -> None:
        """
        Estima cuántos vectores resultarán del TakensEmbedding con la configuración actual
        y avisa si el embedding es extremadamente grande (posible advertencia de costo computacional).

        Usa los atributos de la clase (serie_cols, embedding_dimension, embedding_time_delay, stride)
        para calcular el número de puntos del embedding.

        No devuelve nada; solo imprime o lanza una advertencia.
        """
        n_points = (len(self.serie_cols) - (self.embedding_dimension - 1) * self.embedding_time_delay) // self.stride
        n_points = max(int(n_points), 0)  # nunca puede ser negativo

        if n_points > 1500:
            warnings.warn(
                f"El embedding tendrá {n_points} puntos. "
                "Esto puede ser muy costoso para calcular H1/H2 en TDA."
            )
        else:
            print(f"El embedding tendrá {n_points}")

    def cross_gower_distance(self, df1:pd.DataFrame, df2:pd.DataFrame,
                            categorical_cols:list, numeric_cols:list, weights:list =None) -> pd.DataFrame:
        """
        Calcula la matriz de distancias de Gower entre dos DataFrames "mixtos".

        Comportamiento y suposiciones:
            - df1 y df2 deben contener las columnas 'municipio' y 'estado' que
              se usan para generar identificadores legibles en índices/columnas.
            - Se seleccionan únicamente las columnas listadas en categorical_cols + numeric_cols.
            - Si hay NaNs en las columnas seleccionadas, la función gower manejará
              esos valores según su implementación (recomendar revisar o imputar antes si es crítico).

        Args:
            df1, df2 (pd.DataFrame): DataFrames a comparar (filas de X vs filas de Y).
            categorical_cols (list): columnas categóricas a usar en la distancia.
            numeric_cols (list): columnas numéricas a usar en la distancia.
            weights (list o None): lista de pesos por columna (opcional) para Gower.

        Returns:
            pd.DataFrame: matriz de distancias Gower con índices legibles "Municipio (Estado)".

        Raises:
            ValueError: si ocurre cualquier error durante el cálculo (se encapsula el error original).
        """
        try:
            # Crear identificadores legibles para filas de cada DataFrame
            ids1 = df1['municipio'] + " (" + df1['estado'] + ")"
            ids2 = df2['municipio'] + " (" + df2['estado'] + ")"

            # Filtrar columnas relevantes (categóricas + numéricas)
            X1 = df1[categorical_cols + numeric_cols].copy()
            X2 = df2[categorical_cols + numeric_cols].copy()

            # Calcular matriz de distancias cruzadas con la implementación de gower
            D_cross = gower.gower_matrix(X1, X2, weight=weights)
            del X1, X2

            # Devolver como DataFrame con índices de df1 y columnas de df2
            return pd.DataFrame(D_cross, index=ids1, columns=ids2)
        except Exception as e:
            raise ValueError(f"Ocurrió un error calculando la matriz de Gower: {e}")


    def cross_pairwise_distance(self,df1:pd.DataFrame, df2:pd.DataFrame) -> pd.DataFrame:
        """
        Calcula la matriz de distancias topológicas (PairwiseDistance) entre dos
        conjuntos de series temporales organizadas en DataFrames.

        Flujo:
            - Extrae las columnas de las series (self.serie_cols) y obtiene arrays.
            - Aplica self.pipeline.fit_transform por separado en df1 y df2.
            - Inicializa PairwiseDistance con la métrica elegida, hace fit en X1 (base)
              y transform en X2 (objetivos), obteniendo una matriz cross.

        Args:
            df1, df2 (pd.DataFrame): DataFrames con series en columnas (t0..tN) y
                columnas 'municipio' y 'estado' para generar etiquetas.

        Returns:
            pd.DataFrame: matriz de distancias (filas: df1, columnas: df2) con índices
                y columnas legibles "Municipio (Estado)".
        """
        # Preparar listas de series como arrays (cada fila es una serie)
        X1_series = df1[self.serie_cols].to_numpy()
        X2_series = df2[self.serie_cols].to_numpy()

        # Transform con pipeline (fit_transform independientemente en cada conjunto)
        X1_transformed = self.pipeline.fit_transform(X1_series)
        del X1_series
        X2_transformed = self.pipeline.fit_transform(X2_series)
        del X2_series

        # Calcular distancias cruzadas usando PairwiseDistance
        pairwise = PairwiseDistance(metric=self.metric, n_jobs=-1)
        pairwise.fit(X1_transformed) # fit con X1
        del X1_transformed
        D_cross = pairwise.transform(X2_transformed)
        del X2_transformed

        # Transponer la matriz para que filas correspondan a df1 y columnas a df2
        D_cross = D_cross.T

        # Crear nombres legibles de municipios
        idx = df1['municipio'] + " (" + df1['estado'] + ")"
        cols = df2['municipio'] + " (" + df2['estado'] + ")"

        return pd.DataFrame(D_cross, index=idx, columns=cols)

    def normalization(self,df:pd.DataFrame) -> pd.DataFrame:
        """
        Escala un DataFrame numérico usando el scaler proporcionado en la instancia
        (por defecto MinMaxScaler) y devuelve un nuevo DataFrame con índices y columnas preservados.

        Args:
            df (pd.DataFrame): DataFrame numérico a escalar.

        Returns:
            pd.DataFrame: DataFrame escalado en el rango del scaler (e.g., [0,1]).
        """
        df_scaled = pd.DataFrame(
            self.scaler.fit_transform(df),
            index=df.index,
            columns=df.columns
        )
        return df_scaled

    def row_mean_absolute_difference_matrix(self, df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula la matriz de diferencias absolutas entre los promedios de las filas
        de dos DataFrames. Es una medida simple que resume la discrepancia media
        entre series completas (útil como complemento al TDA).

        Args:
            df1 (pd.DataFrame): Primer DataFrame, cada fila es una serie temporal.
            df2 (pd.DataFrame): Segundo DataFrame, cada fila es una serie temporal.

        Returns:
            pd.DataFrame: Matriz de diferencias absolutas con índices de df1 y columnas de df2.
        """
        idx = df1['municipio'] + " (" + df1['estado'] + ")"
        cols = df2['municipio'] + " (" + df2['estado'] + ")"
        # 1️⃣ Calcular promedios de cada fila
        means1 = df1[self.serie_cols].mean(axis=1).values
        means2 = df2[self.serie_cols].mean(axis=1).values
        # 2️⃣ Crear la matriz de diferencias absolutas usando broadcasting
        diff_matrix = np.abs(means1[:, None] - means2[None, :])
        del means1, means2
        # 3️⃣ Devolver como DataFrame con índices de df1 y columnas de df2
        return pd.DataFrame(diff_matrix, index=idx, columns=cols)

    def hadamard_pairwise_lists(self, distances: list[pd.DataFrame], differences: list[pd.DataFrame]) -> list[pd.DataFrame]:
        """
        Realiza la multiplicación elemento-a-elemento (Hadamard) entre pares de
        DataFrames correspondientes en dos listas.

        Args:
            distances (list of pd.DataFrame): Lista de matrices de distancias (por ejemplo, topológicas).
            differences (list of pd.DataFrame): Lista de matrices de diferencias (por ejemplo, promedios absolutos).

        Returns:
            list of pd.DataFrame: Lista con los DataFrames resultantes de la multiplicación Hadamard.

        Raises:
            ValueError: si las listas no tienen la misma longitud o si algún par no coincide en forma.
        """
        if len(distances) != len(differences):
            raise ValueError("Ambas listas deben tener la misma cantidad de DataFrames.")

        results = []
        for df_dist, df_diff in zip(distances, differences):
            if df_dist.shape != df_diff.shape:
                raise ValueError("Cada par de DataFrames debe tener la misma forma.")
            results.append(df_dist * df_diff)  # Hadamard

        return results
    
    def tda_matrix(self, df1s:list[pd.DataFrame], df2s:list[pd.DataFrame]) -> pd.DataFrame:
        """ 
        Calcula la matriz topológica combinada entre dos listas de DataFrames.

        Cada elemento de df1s/df2s corresponde a una variable distinta (e.g., Tmax, Tmin, Prep).
        Para cada par df1, df2 se calcula:
            - La matriz de distancias TDA (cross_pairwise_distance), normalizada y optimizada.
            - La matriz de diferencia media por fila (row_mean_absolute_difference_matrix), también normalizada.
        Luego se multiplica Hadamard entre cada par (TDA * diff) y se suman los resultados
        para obtener una única matriz topológica compuesta.

        Args:
            df1s (list[pd.DataFrame]): lista de DataFrames fuente (municipios a comparar).
            df2s (list[pd.DataFrame]): lista de DataFrames objetivo (municipios principales).

        Returns:
            pd.DataFrame: matriz resultante de similitud topológica (antes de mezclar con Gower).
        """
        try:
            diffs = []
            topo_matrices = []

            for df1,df2 in zip(df1s,df2s):
                topo_distance_matrix = self.cross_pairwise_distance(df1, df2)
                topo_distance_matrix = self.normalization(topo_distance_matrix)
                topo_distance_matrix = self.size_optimization(topo_distance_matrix)
                topo_matrices.append(topo_distance_matrix)
                del topo_distance_matrix
                diff = self.row_mean_absolute_difference_matrix(df1, df2)
                diff = self.normalization(diff)
                diff = self.size_optimization(diff)
                diffs.append(diff)
                del diff
            gc.collect()
            result =  self.hadamard_pairwise_lists(topo_matrices, diffs)
            result = sum(result)
            return self.size_optimization(result)
        except Exception as e:
            raise ValueError(f"Ocurrió un error calculando la matriz topológica: {e}")
        
    def similarity_index(self, df1s_tda:list[pd.DataFrame], df2s_tda:list[pd.DataFrame],
                        df1_gower:pd.DataFrame, df2_gower:pd.DataFrame, categorical_cols:list, numeric_cols:list,
                        gower_weights:list=None, gamma=1.0) -> pd.DataFrame:
        """
        Combina la información topológica y tabular para obtener una matriz de similitud final.

        Flujo principal:
            1) Calcula D_tda mediante tda_matrix() a partir de las listas de series.
            2) Calcula D_gower mediante cross_gower_distance() a partir de los DataFrames tabulares.
            3) Combina ambas matrices usando weighted_similarity().

        Args:
            df1s_tda, df2s_tda (list[pd.DataFrame]): listas de DataFrames para TDA (cada lista = variables diferentes).
            df1_gower, df2_gower (pd.DataFrame): DataFrames tabulares utilizados por Gower.
            categorical_cols (list): columnas categóricas a considerar en Gower.
            numeric_cols (list): columnas numéricas a considerar en Gower.
            gower_weights (list|None): pesos para las columnas en Gower.
            gamma (float): parámetro gamma para RBF si method='rbf'.

        Returns:
            pd.DataFrame: matriz de similitud final (valores en [0,1]).

        Raises:
            ValueError: encapsula errores internos con mensaje informativo.
        """
        try:    
            D_tda = self.tda_matrix(df1s_tda, df2s_tda)
            D_gower = self.cross_gower_distance(df1_gower,df2_gower,categorical_cols, numeric_cols, gower_weights)
            D_similarity = self.weighted_similarity([D_tda, D_gower],gamma)
            del D_tda, D_gower
            return self.size_optimization(D_similarity)
        except Exception as e:
            raise ValueError(f"Ocurrió un error calculando los índices de similitud: {e}")

    def weighted_similarity(self, distance_matrices:list[pd.DataFrame], gamma=1.0) -> pd.DataFrame:
        """
        Combina múltiples matrices de distancia usando un promedio (posiblemente ponderado)
        y produce una matriz de similitud en rango [0,1].

        Comportamiento:
            - Valida que la lista no esté vacía y que, si se especificaron pesos, su
              longitud coincida con la cantidad de matrices.
            - Verifica que todas las matrices tengan la misma forma.
            - Calcula un promedio ponderado de distancias y, según self.method:
                * 'average': similarity = 1 - distance
                * 'rbf': similarity = exp(-gamma * distance^2)

        Args:
            distance_matrices (list of pd.DataFrame): matrices de distancia a combinar.
            gamma (float): parámetro de la RBF (si aplica).

        Returns:
            pd.DataFrame: matriz de similitud con los mismos índices/columnas que las entradas.

        Raises:
            ValueError: si la lista está vacía, si la cantidad de pesos no coincide
                        o si las matrices difieren en forma.
        """
        n = len(distance_matrices)
        if n == 0:
            raise ValueError("La lista de matrices de distancia está vacía.")

        if self.weights is None:
            self.weights = [1/n] * n
        elif len(self.weights) != n:
            raise ValueError("La cantidad de pesos debe coincidir con la cantidad de matrices.")

        # Verificar que todas las matrices tengan mismos índices y columnas
        idx, cols = distance_matrices[0].index, distance_matrices[0].columns
        for D in distance_matrices:
            if D.shape != distance_matrices[0].shape:
                raise ValueError("Todas las matrices deben tener la misma forma.")

        # Promedio ponderado de distancias
        combined_distance = sum(w * D for w, D in zip(self.weights, distance_matrices))
        if not isinstance(combined_distance, pd.DataFrame):
            combined_distance = pd.DataFrame(combined_distance, index=idx, columns=cols)

        # Calcular similitud
        if self.method == 'average':
            similarity = 1 - combined_distance  # promedio lineal
        elif self.method == 'rbf':
            similarity = np.exp(-gamma * combined_distance**2)  # RBF híbrido
        else:
            raise ValueError("method debe ser 'average' o 'rbf'.")

        if not isinstance(similarity, pd.DataFrame):
            similarity = pd.DataFrame(similarity, index=idx, columns=cols)

        return similarity

    def size_optimization(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convierte columnas de tipo 64-bit (float64 e int64) a sus equivalentes de 32-bit
        (float32 e int32) para reducir uso de memoria y acelerar operaciones.

        Args:
            df (pd.DataFrame): DataFrame original.

        Returns:
            pd.DataFrame: copia del DataFrame con tipos de datos convertidos cuando aplica.

        Nota:
            - Esta función realiza una copia (no modifica in-place) para evitar efectos secundarios.
        """
        df_convertido = df.copy()
        cols_float64 = df_convertido.select_dtypes(include=['float64']).columns
        cols_int64 = df_convertido.select_dtypes(include=['int64']).columns

        df_convertido[cols_float64] = df_convertido[cols_float64].astype('float32')
        df_convertido[cols_int64] = df_convertido[cols_int64].astype('int32')

        return df_convertido

    def plot(self, similarity_df:pd.DataFrame, title:str ="Heatmap de Similitud (Escala Progresiva)") -> None:
        """
        Dibuja un heatmap de similitud usando una escala de color no lineal diseñada
        para resaltar diferencias pequeñas en rangos bajos y ser más intensa cerca de 1.

        Args:
            similarity_df (pd.DataFrame): matriz de similitud (valores en [0,1]).
            title (str): título del gráfico.

        Devuelve:
            None (muestra la figura interactiva con plotly).
        """
        # Escala no lineal: blanco → naranja claro → naranja fuerte → marrón oscuro
        colorscale = [
            [0.00, "#ffffff"],  # blanco
            [0.10, "#fff2e0"],  # casi blanco
            [0.25, "#ffd9b3"],  # naranja muy claro (transición lenta)
            [0.55, "#ffb347"],  # naranja medio
            [0.75, "#ff8c00"],  # naranja fuerte
            [0.90, "#cc6600"],  # naranja oscuro
            [1.00, "#7f2704"]   # marrón profundo
        ]

        fig = px.imshow(
            similarity_df,
            color_continuous_scale=colorscale,
            origin='upper',
            aspect="auto",
            labels=dict(color="Similitud"),
            title=title
        )

        fig.update_layout(
            width=950,
            height=850,
            title_font=dict(size=20, family="Arial", color="black"),
            coloraxis_colorbar=dict(title="Similitud", tickfont=dict(size=12)),
            xaxis=dict(tickangle=45, title=None),
            yaxis=dict(title=None)
        )

        fig.update_xaxes(side="bottom")
        fig.show()

def example():
    """
    Pequeño ejemplo de uso de la clase TDA_similarity.

    NOTAS IMPORTANTES:
        - Este ejemplificador no contiene datos reales; se muestra la estructura de uso.
        - Antes de correrlo: preparar df_series y df_info según los comentarios internos.
    """
    df_series = pd.DataFrame() #Series de tiempo: Es un dataframe con columnas: estado, municipio, variable, t0, ..., t5000
    df_info = pd.DataFrame() #Dataset tabular: Es un dataframe con columnas. estado, municipio, uso_suelo, ph, vegetacion, ...

    #Nota: El dataframe de series de tiempo contiene 3 series de tiempo
    #por cada municipio, es decir, series de tiempo de tmax, tmin y prep del municipio.
    #Por eso, 3 filas son necesarias por cada municipio
    #Nota 2: El dataframe tabular es el que combina edafologia y uso de suelo, este es una fila por municipio

    categorical_cols = ['tipo_zona', 'nivel_riesgo', 'clima', 'tipo_transporte', 'nivel_contaminación'] #Variables categóricas
    numeric_cols = ['poblacion_miles', 'densidad_hab_km2', 'ingreso_promedio',
                    'tasa_criminalidad', 'indice_educativo'] # Variables númericas
    
    #Es necesario asegurarse que los municipios esten en orden, es decir,
    # que el dataframe de tiempo y el tabular, el estado y el municipio coincidan fila a fila
    # estado, municipio                 estado, municipio
    # Aguascalientes, Aguascalientes    Aguascalientes, Aguascalientes

    #Asegurarse que el formato de nombres de municipio sea uniforme
    #evitar: Aguascalientes, ags, aguascalientes, ....

    df2 = df_info.loc[0:5] #Municipios principales 
    df1 = df_info.loc[25:50] #Municipios de los cuales queremos obtener cuales se parecen más a los principales
    del df_info

    df_tmax = df_series[df_series['variable'] == 'Tmax'] #Separamos las series de tiempo Tmax
    df_tmax = df_tmax.reset_index(drop=True)
    df_tmin = df_series[df_series['variable'] == 'Tmin'] #Separamos las series de tiempo de Tmin
    df_tmin = df_tmin.reset_index(drop=True)
    df_prep = df_series[df_series['variable'] == 'Prep'] #Separamos las series de tiempo de Prep
    df_prep = df_prep.reset_index(drop=True)
    serie_cols = list(df_tmax.columns[3:]) #Obtenemos las columnas que son parte de la serie de tiempo
    del df_series

    df2_tmax = df_tmax.loc[0:5] #Municipios principales 
    df1_tmax = df_tmax.loc[25:50] #Municipios de los cuales queremos obtener cuales se parecen más a los principales
    df2_tmin = df_tmin.loc[0:5]
    df1_tmin = df_tmin.loc[25:50]
    df2_prep = df_prep.loc[0:5]
    df1_prep = df_prep.loc[25:50]
    df1s = [df1_tmax, df1_tmin, df1_prep]
    df2s = [df2_tmax, df2_tmin, df2_prep]

    dimension = 100
    time_delay = 10
    stride = 10

    similarity = TDA_similarity(serie_cols=serie_cols, embedding_dimension=dimension,
                               embedding_time_delay=time_delay, stride=stride)
    
    #Creamos la clase, esta te avisa si tu configuración del TakensEmbbeding no es óptima
    #computacionalmente para calcular la persistencia homologica
    #El parámetro weights indica si quieres darle más peso a lo de TDA o a lo tabular
    #weights[0.7,0.3] significa que el 70% viene del TDA y el 30% del s

    D = similarity.similarity_index(df1s, df2s, df1, df2, categorical_cols, numeric_cols)
    #La matriz D indica que tan similares son los municipios, cada columna es un municipio principal.
    #la similitud va de 0 a 1. "0" significa que no son nada similares y "1" que son iguales
    similarity.plot(D)

if __name__ == "__main__":
    example()