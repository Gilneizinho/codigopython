import numpy as np
import pyaudio
import scipy.signal as signal
import matplotlib.pyplot as plt
import time

# Parâmetros de áudio
fs = 44100 # Define a taxa de amostragem 44100 heartz	
duration = 0.2 # Define a duração de cada bit

# Instância do PyAudio
p = pyaudio.PyAudio() 

# Parâmetros para tratar ruídos e término do som 	
nao_capturar = 0.002 # Não captura ruidos abaixo de 0.002, amplitude baixa 
silence = 2 # Define uma taxa de silêncio após ler os 8 bits para saber se o emissor terminou de enviar os bits

# Criação do fluxo de áudio
stream = p.open(format=pyaudio.paFloat32, channels=1, rate=fs, input=True)

# Retificador de sinal
def retificador(signal):
    return np.abs(signal) # Função do numpy que retira os sinais negativos, deixando somente os positivos
    
# Detector de envelope
def detector_de_envelope(sinal_retificado, fs, frequencia_de_corte=100): # Filtro butterworth de 2° ordem
    b, a = signal.butter(2, frequencia_de_corte / (fs / 2)) # Guarda na variável b os coeficientes do numerador do filtro e na variável a os coeficientes do denominador
    envelope = signal.filtfilt(b, a, sinal_retificado) # Aplica o filtro construído acima das variáveis a e b e salva o resultado na variável envelope
    return envelope
    
# Converte o valor da tabela ASCII para o caractere correspondente 
def converter(bits):
    byte_str = ''.join(str(bit) for bit in bits)  # Itera sobre a lista de bits	
    return chr(int(byte_str, 2)) # Converte o número binário no caractere correspondente
    

pacote = [] # Guarda os bits do valor transmitido pelo emissor
receiver = False # Define se está sendo recebido um novo conjunto de 8 bits
tempo_ultima_transmissao = time.time() # Pega o tempo da última transmissão de bits para no final poder printar a palavra 
palavra = "" # Variável palavra inicialmente começa vazia

# Loop principal
try:
    while True:
        entrada = np.frombuffer(stream.read(int(fs * duration)), dtype=np.float32) # Lê os bits recebidos pelo emissor e os guarda num array, como são 44100 heartz e 0.2s, resulta em 8820 amostras no vetor
        sinal_retificado = retificador(entrada) # Chama a função retificador para retificar o sinal de entrada, deixando somente os picos positivos do sinal
        sinal_demodulado = detector_de_envelope(sinal_retificado, fs) # Chama a função detector de envelope para aplicar o filtro passa baixa (butterworth de 2° ordem) 
        amplitude_media = np.mean(sinal_demodulado) # Retorna a média dos elementos do vetor onde estão os sinais
        if amplitude_media > nao_capturar: # Filtra entre os ruídos do sistema e o sinal de fato a ser transmitido
            if not receiver: # Se for a primeira vez a enviar a cadeia de 8 bits, entra no if
                if amplitude_media > 0.5: # Se amplitude media for maior que 0.5, o bit é detectado como 1, abaixo é detectado como 0
                    print("Bit 1 detectado!") # Printa na tela que o bit 1 foi detectado
                    receiver = True # Receiver vira true indicando que uma cadeia de 8 bits foi iniciada
            else:
                bit = int(amplitude_media > 0.5) # Define se o bit irá ser 0 ou 1 baseado no valor da amplitude média
                pacote.append(bit) # Adiciona o valor do bit na lista pacote
                if len(pacote) == 8: # Se o tamanho da lista pacote corresponder ao tamanho da cadeia de 8 bits válida enviada pelo emissor, entra no if e encerra aquela cadeia.  
                    print("Bit 0 detectado!")
                    tempo_ultima_transmissao = time.time() # Registra o tempo da transmissão atual
                    m = converter(pacote) # Chama a função converter para que a cadeia de 8 bits seja convertido ao caractere correspondente
                    palavra += m # Incrementa a variável palavra com o caractere convertido anteriormente
                    pacote.clear() # Esvazia a lista pacote
                    receiver = False # Valor booleano de receiver troca para False, indicando que uma nova cadeia de 8 bits pode ser lida
        if time.time() - tempo_ultima_transmissao > silence and palavra: # Se o tempo atual menos o tempo da última transmissão for maior que o tempo de silêncio e da palavra, entra no if
            print("Palavra recebida:","".join(palavra)) # Printa a palavra completa na tela
            palavra = "" # Define a variável palavra como vazia
except KeyboardInterrupt:
    pass
    
# Quando o loop é interrompido, o programa fecha o fluxo de áudio e termina a instância do PyAudio
stream.stop_stream()
stream.close()
p.terminate()
