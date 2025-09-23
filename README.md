# Sistema de Monitoramento de Fábrica 🏭

Um sistema distribuído de monitoramento de sensores para fábricas inteligentes usando **Apache Kafka**, **Docker** e **Python**. Este projeto implementa um pipeline escalável de processamento de dados IoT seguindo padrões modernos de sistemas distribuídos.

## 🎯 Visão Geral do Projeto

Este sistema simula e monitora dados de sensores de um ambiente de fábrica inteligente, processando fluxos de dados em tempo real para detectar anomalias e gerar alertas. A arquitetura demonstra conceitos-chave de sistemas distribuídos incluindo:

- **Arquitetura orientada a eventos** com Apache Kafka
- **Microsserviços containerizados** com Docker
- **Processamento de dados em tempo real** e detecção de anomalias
- **Padrões escaláveis producer-consumer**
- **Balanceamento de carga** e failover automático
- **Monitoramento em tempo real** e observabilidade
- **Demonstração de tolerância a falhas**

## 🏗️ Arquitetura

```mermaid
graph TB
    subgraph "Sensor Producers"
        SP1[Temperature Sensor]
        SP2[Vibration Sensor] 
        SP3[Energy Sensor]
    end
    
    subgraph "Kafka Cluster"
        K1[Kafka Broker 1]
        K2[Kafka Broker 2]
        K3[Kafka Broker 3]
        UI[Kafka UI]
    end
    
    subgraph "Data Consumers"
        C1[Consumer 1]
        C2[Consumer 2]
        C3[Consumer 3]
    end
    
    subgraph "Storage & Monitoring"
        PG[PostgreSQL]
        MS[Monitoring Service<br/>Backend]
    end
    
    %% Each producer can connect to all Kafka brokers
    SP1 --> K1
    SP1 --> K2
    SP1 --> K3
    SP2 --> K1
    SP2 --> K2
    SP2 --> K3
    SP3 --> K1
    SP3 --> K2
    SP3 --> K3
    
    %% Each consumer can connect to all Kafka brokers
    C1 --> K1
    C1 --> K2
    C1 --> K3
    C2 --> K1
    C2 --> K2
    C2 --> K3
    C3 --> K1
    C3 --> K2
    C3 --> K3
    
    %% Each consumer writes to PostgreSQL
    C1 --> PG
    C2 --> PG
    C3 --> PG
    
    %% Monitoring service reads from PostgreSQL
    MS --> PG
```

## 🚀 Início Rápido

### Pré-requisitos

- Docker
- Make (para comandos de conveniência)

### 1. Início Rápido - Tudo de Uma Vez

```bash
# Construir e iniciar sistema completo (recomendado para a primeira run)
make all
```

Abrir [dashboard](http://localhost:5000) de monitoramento - http://localhost:5000

Abrir [Kafka UI](http://localhost:8080) - http://localhost:8080

### 2. Configuração Passo a Passo

```bash
# Iniciar apenas infraestrutura
make start

# Iniciar produtores de sensores
make start-producers

# Iniciar consumidores de dados
make start-consumers

# Iniciar dashboard de monitoramento
make start-monitoring
```

### 3. Opções Alternativas de Inicialização

```bash
# Infraestrutura + produtores apenas (sem consumidores)
make infrastructure-only

# Infraestrutura + produtores + consumidores (sem monitoramento)
make with-consumers

# Sistema completo com monitoramento
make with-monitoring
```

### 4. Monitorar Dados em Tempo Real

```bash
# Ver logs dos produtores no docker
make logs-producers

# Ver logs dos consumidores no docker  
make logs-consumers

# Monitorar fluxo de dados dos sensores
make monitor-sensors

# Monitorar alertas
make monitor-alerts
```

Abrir [dashboard](http://localhost:5000) de monitoramento - http://localhost:5000

Abrir [Kafka UI](http://localhost:8080) - http://localhost:8080

## 📊 Componentes do Sistema

### Produtores de Sensores

**Producer Unificado Único** (`src/producers/sensor_producer.py`):
- **Configuração orientada por ambiente**: Alterar tipo de sensor via variável `SENSOR_TYPE`
- **Múltiplos tipos de sensores**: temperature, vibration, energy, humidity, pressure
- **Simulação de dados realística**: Padrões baseados em tempo, ruído, anomalias
- **Geração de alertas**: Detecção automática de limites de warning/critical
- **Amostragem configurável**: Intervalos diferentes por tipo de sensor
- **Monitoramento de saúde**: Reporta status para banco de dados de monitoramento

### Consumidores de Dados

**Consumer Unificado Único** (`src/consumers/sensor_consumer.py`):
- **Balanceamento de carga**: Atribuição automática de partições dentro do grupo de consumidores
- **Detecção de anomalias**: Geração de alertas baseada em limites em tempo real
- **Processamento genérico**: Manipula todos os tipos de sensores no mesmo código
- **Tolerância a falhas**: Rebalanceamento automático quando consumidores entram/saem
- **Monitoramento de saúde**: Reporta status e atribuições de partições para banco de monitoramento
- **Persistência de dados**: Armazena dados processados e alertas no PostgreSQL

### Infraestrutura Kafka

**Cluster KRaft de 3 Nós**:
- **Kafka moderno**: Sem dependência do ZooKeeper (modo KRaft)
- **Alta disponibilidade**: 3 brokers com fator de replicação 2
- **Tópicos**: `sensor-data` (3 partições), `alerts` (2 partições)
- **Acesso externo**: Portas 9092, 9094, 9096
- **Distribuição de carga**: Qualquer produtor pode enviar para qualquer broker, qualquer broker pode rotear para qualquer consumidor

### Monitoramento & Observabilidade

**Dashboard de Monitoramento em Tempo Real** (`src/monitoring/monitoring_service.py`):
- **Backend Flask**: API REST fornecendo métricas do sistema em tempo real
- **Frontend Web**: Dashboard responsivo com auto-refresh
- **Saúde do Sistema**: Monitoramento de status e heartbeat de consumidores/produtores
- **Rastreamento de Partições**: Visualização em tempo real da atribuição de partições
- **Eventos de Rebalanceamento**: Monitoramento ao vivo do rebalanceamento de consumidores
- **Métricas de Performance**: Estatísticas de throughput e processamento
- **Demo de Tolerância a Falhas**: Demonstração visual da resiliência do sistema

### Armazenamento de Dados

- **PostgreSQL 15**: Dados processados, alertas e informações de monitoramento

## 🛠️ Comandos de Desenvolvimento

| Comando | Descrição |
|---------|-------------|
| **Início Rápido** |
| `make all` | **Construir e iniciar sistema completo (infraestrutura + produtores + consumidores + monitoramento)** |
| `make help` | Mostrar todos os comandos disponíveis |
| `make setup` | Inicializar ambiente e formatar armazenamento Kafka |
| **Gerenciamento de Infraestrutura** |
| `make start` | Iniciar apenas serviços de infraestrutura (Kafka + PostgreSQL + Kafka UI) |
| `make infrastructure-only` | Iniciar infraestrutura + produtores (sem consumidores, sem monitoramento) |
| `make with-consumers` | Iniciar infraestrutura + produtores + consumidores (sem monitoramento) |
| `make with-monitoring` | Iniciar sistema completo com dashboard de monitoramento |
| `make stop` | Parar todos os serviços |
| `make clean` | Remover containers e volumes |
| `make status` | Verificar status dos serviços |
| `make health` | Verificar saúde dos serviços |
| **Gerenciamento de Componentes** |
| `make build-all` | Construir todas as imagens Docker |
| `make build-producers` | Construir imagens dos produtores de sensores |
| `make build-consumers` | Construir imagens dos consumidores |
| `make start-producers` | Iniciar produtores de sensores |
| `make stop-producers` | Parar produtores de sensores |
| `make start-consumers` | Iniciar instâncias de consumidores |
| `make stop-consumers` | Parar instâncias de consumidores |
| `make start-monitoring` | Iniciar dashboard de monitoramento |
| **Monitoramento & Debug** |
| `make logs-producers` | Ver logs dos produtores de sensores |
| `make logs-consumers` | Ver logs dos consumidores |
| `make monitor-sensors` | Monitorar dados de sensores em tempo real |
| `make monitor-alerts` | Monitorar alertas em tempo real |
| **Testes & Verificação** |
| `make test-external` | Testar conectividade externa |

## ⚙️ Configuração

### Configuração dos Sensores

Cada tipo de sensor tem faixas realísticas e limites predefinidos

Estes limites podem ser configurados no nosso arquivo `.env`

```python
sensor_configs = {
    "temperature": {
        "base_value": 25.0,      # °C
        "warning_threshold": 35.0,
        "critical_threshold": 40.0,
        "sampling_interval": 3.0  # seconds
    },
    "vibration": {
        "base_value": 2.0,       # mm/s  
        "warning_threshold": 5.0,
        "critical_threshold": 7.0,
        "sampling_interval": 4.0
    },
    "energy": {
        "base_value": 100.0,     # kW
        "warning_threshold": 150.0, 
        "critical_threshold": 180.0,
        "sampling_interval": 10.0
    }
}
```

### Variáveis de Ambiente

```bash
# Sensor Configuration
SENSOR_ID=temp-sensor-001
SENSOR_TYPE=temperature
SAMPLING_INTERVAL=3.0
FACTORY_SECTION=production
MACHINE_ID=machine-001
ZONE=zone-a

# Consumer Configuration
CONSUMER_ID=consumer-001
CONSUMER_GROUP=sensor-processors

# Kafka Configuration  
KAFKA_BROKERS=kafka1:29092,kafka2:29092,kafka3:29092
SENSOR_TOPIC=sensor-data
ALERT_TOPIC=alerts

# Database Configuration
DATABASE_URL=postgresql://factory_user:factory_pass@postgres:5432/factory_monitoring

# Monitoring Configuration
MONITORING_HOST=0.0.0.0
MONITORING_PORT=5000
```

### Exemplo de Dados do Sensor

```json
{
  "timestamp": "2025-09-16T21:41:41.011144Z",
  "sensor_id": "temp-sensor-001",
  "sensor_type": "temperature", 
  "location": {
    "factory_section": "production",
    "machine_id": "machine-001",
    "zone": "zone-a"
  },
  "value": 42.48,
  "unit": "°C",
  "alert_level": "critical",
  "quality": 1.0,
  "metadata": {
    "reading_count": 14,
    "warning_threshold": 35.0,
    "critical_threshold": 40.0
  }
}
```

## 📈 Fluxo de Dados & Sistema de Alertas

### Balanceamento de Carga & Tolerância a Falhas
1. **Distribuição de Produtores**: Qualquer sensor pode enviar dados para qualquer broker Kafka
2. **Balanceamento de Carga dos Consumidores**: Kafka distribui automaticamente partições entre consumidores disponíveis
3. **Rebalanceamento Automático**: Quando consumidores entram/saem, partições são automaticamente reatribuídas
4. **Monitoramento de Saúde**: Rastreamento em tempo real da saúde e status de produtores/consumidores
5. **Demonstração de Failover**: Mate containers para ver o sistema se adaptar e recuperar

### Níveis de Alerta
- **Normal**: Valor dentro da faixa esperada
- **Warning**: 15% de probabilidade, valor próximo ao limite de warning  
- **Critical**: 5% de probabilidade, valor próximo/acima do limite crítico

### Processamento em Tempo Real
1. Sensores geram leituras a cada 3-10 segundos
2. Dados publicados no tópico Kafka `sensor-data` (balanceamento de carga entre brokers)
3. Consumidores processam dados para detecção de anomalias (balanceamento de carga via atribuição de partições)
4. Alertas gerados para violações de limites e publicados no tópico `alerts`
5. Dados processados e metadados armazenados no PostgreSQL
6. Dashboard de monitoramento fornece visibilidade em tempo real do comportamento do sistema

### Recursos de Monitoramento
- **Status do Sistema**: Saúde em tempo real de todos os produtores e consumidores
- **Atribuições de Partições**: Visualização ao vivo de quais consumidores estão manipulando quais partições
- **Eventos de Rebalanceamento**: Demonstração visual da tolerância a falhas do Kafka
- **Métricas de Performance**: Throughput, taxas de processamento e estatísticas do sistema
- **Rastreamento de Alertas**: Exibição em tempo real de detecção de anomalias e geração de alertas

## 🔧 Monitoramento & Observabilidade

### Dashboard em Tempo Real
Acessar o dashboard de monitoramento em **http://localhost:5000**

**Recursos**:
- **Status do Sistema**: Indicadores de saúde ao vivo para todos os componentes
- **Saúde dos Consumidores**: Status de consumidores em tempo real com atribuições de partições
- **Saúde dos Produtores**: Status de conexão dos produtores e taxas de mensagens
- **Eventos de Rebalanceamento**: Visualização ao vivo do rebalanceamento de consumidores Kafka
- **Métricas de Performance**: Estatísticas de throughput e performance do sistema
- **Demo de Tolerância a Falhas**: Demonstração visual da resiliência do sistema

**Endpoints da API**:
- `GET /api/system-status` - Visão geral da saúde do sistema
- `GET /api/consumer-health` - Status dos consumidores e atribuições de partições
- `GET /api/producer-health` - Status dos produtores e taxas de mensagens
- `GET /api/partition-assignment` - Atribuições de partições atuais e atividade
- `GET /api/real-time-metrics` - Métricas de throughput em tempo real
- `GET /api/recent-alerts` - Alertas de anomalias recentes e eventos de rebalanceamento

### Teste de Tolerância a Falhas

**Iniciar sistema completo com monitoramento**:
```bash
make all
```

**Testar falha de consumidor** (observar rebalanceamento no dashboard):
```bash
# Matar um consumidor e observar reatribuição de partições
docker kill consumer-1
```

**Testar falha de produtor** (observar mudança no status de saúde):
```bash
# Matar um produtor e observar indicadores de saúde
docker kill temperature-sensor
```

**Monitorar eventos de rebalanceamento em tempo real**:
```bash
# Ver eventos de rebalanceamento conforme acontecem
make monitor-alerts
```

### Esquema do Banco de Dados

- `consumer_health`: Status de consumidores, heartbeats, atribuições de partições
- `producer_health`: Status de produtores, heartbeats, taxas de mensagens
- `rebalancing_events`: Rastreamento de eventos de rebalanceamento em tempo real
- `sensor_readings`: Dados de sensores processados com metadados
- `alerts`: Alertas gerados e resultados de detecção de anomalias

## 🧪 Testes & Verificação

```bash
# Testar conectividade Kafka
make test-external

# Testar operações de tópicos
make test-topics

# Monitorar tipo específico de sensor
docker compose logs -f temperature-sensor

# Testar tolerância a falhas - matar um consumidor e observar rebalanceamento
docker kill consumer-1
# Observar reatribuição de partições em tempo real

# Testar falha de produtor - matar um sensor e observar status de saúde
docker kill vibration-sensor  
# Observar mudança na saúde do produtor

# Monitorar eventos de rebalanceamento em tempo real
make monitor-alerts
```

## 📂 Estrutura do Projeto

```
.
├── src/
│   ├── producers/
│   │   └── sensor_producer.py      # Unified sensor simulator
│   ├── consumers/
│   │   └── sensor_consumer.py      # Unified data processor  
│   └── monitoring/
│       ├── monitoring_service.py   # Flask backend API
│       └── templates/
│           └── dashboard.html      # Real-time web dashboard
├── docker/
│   ├── Dockerfile.producer         # Sensor container image
│   ├── Dockerfile.consumer         # Consumer container image
│   └── Dockerfile.monitoring       # Monitoring service image
├── docker-compose.yml              # Multi-service orchestration
├── Makefile                        # Development commands
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```
