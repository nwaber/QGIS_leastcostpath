"""
Model exported as python.
Name : "Cost Surface"
Group : "NHW scripts"
With QGIS : 32802
"""

#Version 0.01
#2023-04-16

from PyQt5.QtCore import QCoreApplication
import numpy
import math
# Import the processing module
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterDefinition,
                       QgsProcessingParameterFolderDestination,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterRasterDestination)
import processing


# Define the class for the algorithm
class CostSurface(QgsProcessingAlgorithm):

    # Define the input and output parameters
    INPUT = 'INPUT'
    METHOD = 'METHOD'
    OUTPUT = 'OUTPUT'

    def __init__(self):
        super().__init__()
        self.ADVANCED = 'ADVANCED'
        self.BODY_WEIGHT = 'BODY_WEIGHT'
        self.LOAD_WEIGHT = 'LOAD_WEIGHT'
        self.WALKING_SPEED = 'WALKING_SPEED'

    # Define the methods for the cost calculation
    methods = ['tobler', 'herzog', 'sullivan', 'pandolf', 'minetti', 'tobler offpath', 'davey', 'rees', 'irmischer-clarke male', 'irmischer-clarke offpath male', 'irmischer-clarke female', 'irmischer-clarke offpath female', 'llobera-sluckin', 'campbell']

    # Define the initAlgorithm method to add the parameters
    def initAlgorithm(self, config=None):
        # Add a raster layer parameter for the slope input
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT,
                self.tr('Slope input')
            )
        )
        # Add an enum parameter for the method selection
        self.addParameter(
            QgsProcessingParameterEnum(
                self.METHOD,
                self.tr('Method'),
                self.methods
            )
        )
        # Add a raster layer parameter for the cost output
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT,
                self.tr('Cost surface')
            )
        )
        
        self.addParameter(QgsProcessingParameterFolderDestination(
            self.ADVANCED,
            self.tr('Advanced'),
            optional=True
        ))
        
        
        self.addParameter(QgsProcessingParameterNumber(
            self.BODY_WEIGHT,
            self.tr('Body weight (kg)'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=80,
            minValue=0,
            maxValue=200
        ))

        self.addParameter(QgsProcessingParameterNumber(
            self.LOAD_WEIGHT,
            self.tr('Load weight (kg)'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=20,
            minValue=0,
            maxValue=100
        ))

        self.addParameter(QgsProcessingParameterNumber(
            self.WALKING_SPEED,
            self.tr('Walking speed (km/h)'),
            type=QgsProcessingParameterNumber.Double,
            defaultValue=5,
            minValue=1,
            maxValue=10
        ))        

    # Define the processAlgorithm method to execute the algorithm
    def processAlgorithm(self, parameters, context, feedback):
        # Get the input and output parameters
        input = self.parameterAsRasterLayer(
            parameters,
            self.INPUT,
            context
        )
        method = self.parameterAsEnum(
            parameters,
            self.METHOD,
            context
        )
        output = self.parameterAsOutputLayer(
            parameters,
            self.OUTPUT,
            context
        )

        body_weight = self.parameterAsDouble(parameters, self.BODY_WEIGHT, context)
        load_weight = self.parameterAsDouble(parameters, self.LOAD_WEIGHT, context)
        walking_speed = self.parameterAsDouble(parameters, self.WALKING_SPEED, context)
        # Convert from km/h to m/s
        walking_speed = walking_speed / 3.6

        # Calculate the cost surface using the selected method
        if method == 0: # tobler
            # Use the gdal:rastercalculator algorithm with a tobler expression
            expression = '6 * exp(-3.5 * abs(numpy.tan(A * 0.0174533) + 0.05))'
            alg_params = {
                'INPUT_A': input,
                'BAND_A': 1,
                'FORMULA': expression,
                'OUTPUT': output
            }            
            processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback)

        elif method == 1: # herzog
            # Use the gdal:rastercalculator algorithm with a herzog expression
            expression = '(1.5 * A + 2.4) * (A <= 10) + (2.9 * A - 14.4) * ((A > 10) & (A <= 20)) + (6.2 * A - 64) * ((A > 20) & (A <= 30)) + (11.5 * A - 166) * ((A > 30) & (A <= 45)) + 1000 * (A > 45)'
            alg_params = {
                'INPUT_A': input,
                'BAND_A': 1,
                'FORMULA': expression,
                'OUTPUT': output
            }            
            processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback)

        elif method == 2: # sullivan
            # Use the gdal:rastercalculator algorithm with a sullivan expression
            expression = 'numpy.power(1 / cos(A * 0.0174533) , 0.1)'
            alg_params = {
                'INPUT_A': input,
                'BAND_A': 1,
                'FORMULA': expression,
                'OUTPUT': output
            }
            processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback)

        elif method == 3: # pandolf
            # Use the gdal:rastercalculator algorithm with a pandolf expression
            expression = '(1.5 * W + 2 + L) * (1.5 / V ** 0.5) * ((1.5 * W + L + W * L / (33.3 - L)) / W) ** 2 * (1 + G)'
            # Define the parameters for the pandolf formula
            W = body_weight # body weight in kg
            L = load_weight # load weight in kg
            V = walking_speed # walking speed in m/s
            G = 'numpy.tan(A * 0.0174533)' # slope gradient
            # Replace the parameters in the expression with their values
            expression = expression.replace('W', str(W))
            expression = expression.replace('L', str(L))
            expression = expression.replace('V', str(V))
            expression = expression.replace('G', 'numpy.tan(A * 0.0174533)')
            alg_params = {
                'INPUT_A': input,
                'BAND_A': 1,
                'FORMULA': expression,
                'OUTPUT': output
            }
            processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback)
            
        elif method == 4: # minetti
            # Use the gdal:rastercalculator algorithm with a minetti expression
            expression = '1 + 0.05 * A + 0.0065 * A ** 2'
            alg_params = {
                'INPUT_A': input,
                'BAND_A': 1,
                'FORMULA': expression,
                'OUTPUT': output
            }
            processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback)

        elif method == 5: # tobler offpath
            # Use the gdal:rastercalculator algorithm with a tobler offpath expression
            expression = '6 * exp(-3.5 * abs(numpy.tan(A * 0.0174533) + 0.05)) * 0.6'
            alg_params = {
                'INPUT_A': input,
                'BAND_A': 1,
                'FORMULA': expression,
                'OUTPUT': output
            }
            processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback)
            
        elif method == 6: # davey
            # Use the gdal:rastercalculator algorithm with a davey expression
            expression = '(1.5 * W + 2 + L) * (1.5 / V ** 0.5) * ((1.5 * W + L + W * L / (33.3 - L)) / W) ** 2 * (1 + G) * (1 + 0.25 * G ** 2)'
            # Define the parameters for the davey formula
            W = body_weight # body weight in kg
            L = load_weight # load weight in kg
            V = walking_speed # walking speed in m/s
            G = 'numpy.tan(A * 0.0174533)' # slope gradient
            # Replace the parameters in the expression with their values
            expression = expression.replace('W', str(W))
            expression = expression.replace('L', str(L))
            expression = expression.replace('V', str(V))
            expression = expression.replace('G', 'numpy.tan(A * 0.0174533)')
            alg_params = {
                'INPUT_A': input,
                'BAND_A': 1,
                'FORMULA': expression,
                'OUTPUT': output
            }
            processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback)
            
        elif method == 7: # rees
            # Use the gdal:rastercalculator algorithm with a rees expression
            expression = '(1.5 * W + 2 + L) * (1.5 / V ** 0.5) * ((1.5 * W + L + W * L / (33.3 - L)) / W) ** 2 * (1 + G) * (1 + G ** 2)'
            # Define the parameters for the rees formula
            W = body_weight # body weight in kg
            L = load_weight # load weight in kg
            V = walking_speed # walking speed in m/s
            G = 'numpy.tan(A * 0.0174533)' # slope gradient
            # Replace the parameters in the expression with their values
            expression = expression.replace('W', str(W))
            expression = expression.replace('L', str(L))
            expression = expression.replace('V', str(V))
            expression = expression.replace('G', 'numpy.tan(A * 0.0174533)')
            alg_params = {
                'INPUT_A': input,
                'BAND_A': 1,
                'FORMULA': expression,
                'OUTPUT': output
            }
            processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback)

        elif method == 8: # irmischer-clarke male
            # Use the gdal:rastercalculator algorithm with an irmischer-clarke male expression
            expression = '0.2 + 1.8 * exp(0.215 * A)'
            alg_params = {
                'INPUT_A': input,
                'BAND_A': 1,
                'FORMULA': expression,
                'OUTPUT': output
            }
            processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback)
        elif method == 9: # irmischer-clarke offpath male
            # Use the gdal:rastercalculator algorithm with an irmischer-clarke offpath male expression
            expression = '(0.2 + 1.8 * exp(0.215 * A)) * 1.5'
            alg_params = {
                'INPUT_A': input,
                'BAND_A': 1,
                'FORMULA': expression,
                'OUTPUT': output
            }
            processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback)
        elif method == 10: # irmischer-clarke female
            # Use the gdal:rastercalculator algorithm with an irmischer-clarke female expression
            expression = '0.2 + 1.8 * exp(0.185 * A)'
            alg_params = {
                'INPUT_A': input,
                'BAND_A': 1,
                'FORMULA': expression,
                'OUTPUT': output
            }
            processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback)
        elif method == 11: # irmischer-clarke offpath female
            # Use the gdal:rastercalculator algorithm with an irmischer-clarke offpath female expression
            expression = '(0.2 + 1.8 * exp(0.185 * A)) * 1.5'
            alg_params = {
                'INPUT_A': input,
                'BAND_A': 1,
                'FORMULA': expression,
                'OUTPUT': output
            }
            processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback)

        elif method == 12: # llobera-sluckin
            # Use the gdal:rastercalculator algorithm with a llobera-sluckin expression
            expression = '1 / (1 + exp(-0.5 * (A - 10)))'
            alg_params = {
                'INPUT_A': input,
                'BAND_A': 1,
                'FORMULA': expression,
                'OUTPUT': output
            }
            processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback)
            
        elif method == 13: # campbell
            # Use the gdal:rastercalculator algorithm with a campbell expression
            expression = '(1.5 * W + 2 + L) * (1.5 / V ** 0.5) * ((1.5 * W + L + W * L / (33.3 - L)) / W) ** 2 * (1 + G) * (1 + G ** 2) * (1 + G ** 4)'
            # Define the parameters for the campbell formula
            W = body_weight # body weight in kg
            L = load_weight # load weight in kg
            V = walking_speed # walking speed in m/s
            G = 'numpy.tan(A * 0.0174533)' # slope gradient
            # Replace the parameters in the expression with their values
            expression = expression.replace('W', str(W))
            expression = expression.replace('L', str(L))
            expression = expression.replace('V', str(V))
            expression = expression.replace('G', 'numpy.tan(A * 0.0174533)')
            alg_params = {
                'INPUT_A': input,
                'BAND_A': 1,
                'FORMULA': expression,
                'OUTPUT': output
            }
            processing.run('gdal:rastercalculator', alg_params, context=context, feedback=feedback)

        # Return the output
        return {self.OUTPUT: output}


    # Define the name and group methods to display the algorithm in QGIS
    def name(self):
        return 'costsurface'

    def displayName(self):
        return self.tr('Cost Surface')

    def group(self):
        return self.tr('NHW scripts')

    def groupId(self):
        return 'NHWscripts'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return CostSurface()
