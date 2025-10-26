# Tsuru Groups 🚀

**Tsuru Groups** é um microsaas desenvolvido em Django para agendamento e envio de mensagens em massa para grupos do WhatsApp. A plataforma oferece planos de assinatura por usuário, permitindo que cada cliente conecte seu WhatsApp e gerencie campanhas de mensagens de forma automatizada.

## 🎯 Funcionalidades

- **Autenticação e Contas**: Sistema completo de registro, login e gerenciamento de usuários
- **Integração WhatsApp**: Conexão com API Uazapi para envio de mensagens
- **Agendamento Inteligente**: Sistema de agendamento com delays configuráveis entre mensagens
- **Templates de Mensagens**: Criação e reutilização de templates personalizados
- **Sistema de Assinatura**: Planos com limites diferenciados usando Stripe
- **Dashboard Analytics**: Estatísticas e métricas de campanhas
- **API REST**: API completa para integrações externas
- **Filas de Tarefas**: Processamento assíncrono com RQ/Redis

## 🏗️ Arquitetura

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Django API    │    │   WhatsApp API  │
│   (React/Vue)   │◄──►│   (REST API)     │◄──►│    (Uazapi)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │      Redis       │    │    Stripe API   │
│   (Database)    │    │  (Cache/Queue)   │    │   (Payments)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📦 Tecnologias

- **Backend**: Django 5.0+ com Django REST Framework
- **Banco de Dados**: PostgreSQL
- **Cache/Filas**: Redis + RQ
- **Autenticação**: Django Allauth + Token Auth
- **Pagamentos**: Stripe
- **Integração WhatsApp**: API Uazapi
- **Deploy**: Docker + Docker Compose
- **Gerenciamento de Dependências**: Poetry

## 🚀 Instalação e Setup

### Pré-requisitos

- Python 3.10+
- Poetry
- PostgreSQL
- Redis
- Docker e Docker Compose (opcional)

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/tsuru-groups.git
cd tsuru-groups
```

### 2. Instale as dependências

```bash
poetry install
poetry shell
```

### 3. Configure as variáveis de ambiente

```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

### 4. Execute as migrações

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5. Execute o servidor

```bash
python manage.py runserver
```

### 6. Execute os workers (em terminais separados)

```bash
# Worker para tarefas gerais
python manage.py rqworker default

# Worker para agendamento
python manage.py rqworker scheduling

# Scheduler para tarefas agendadas
python manage.py rqscheduler
```

## 🐳 Deploy com Docker

### Desenvolvimento

```bash
docker-compose up -d
```

### Produção

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 📊 Estrutura do Projeto

```
tsuru_groups/
├── apps/
│   ├── accounts/          # Gerenciamento de usuários
│   ├── whatsapp/          # Integração WhatsApp
│   ├── scheduling/        # Agendamento de mensagens
│   ├── subscriptions/     # Sistema de assinaturas
│   └── core/              # Funcionalidades base
├── tsuru_groups/          # Configurações Django
├── templates/             # Templates HTML
├── static/                # Arquivos estáticos
├── media/                 # Uploads de arquivos
└── tests/                 # Testes automatizados
```

## 🔧 Configuração da API WhatsApp

### 1. Criar Instância

```python
POST /api/v1/whatsapp/instances/
{
    "name": "Minha Instância",
    "gateway_url": "https://sua-api-uazapi.com",
    "api_key": "sua-chave-api"
}
```

### 2. Conectar WhatsApp

```python
POST /api/v1/whatsapp/instances/{id}/connect/
{
    "phone": "5511999999999"  # Opcional
}
```

### 3. Criar Mensagem Agendada

```python
POST /api/v1/scheduling/scheduled-messages/
{
    "name": "Campanha de Natal",
    "message_content": "🎄 Feliz Natal! Aproveite nossas ofertas especiais!",
    "schedule_date": "2024-12-25",
    "schedule_time": "09:00:00",
    "groups": [1, 2, 3],
    "contacts": [4, 5, 6],
    "delay_min": 3,
    "delay_max": 6
}
```

## 💰 Planos de Assinatura

### Basic
- 1 Instância WhatsApp
- 100 mensagens/mês
- 10 grupos por instância
- 1.000 contatos
- 10 templates

### Premium
- 3 Instâncias WhatsApp
- 1.000 mensagens/mês
- 50 grupos por instância
- 10.000 contatos
- 50 templates
- Acesso à API
- Webhook support

### Enterprise
- Instâncias ilimitadas
- 10.000 mensagens/mês
- Grupos ilimitados
- Contatos ilimitados
- Templates ilimitados
- Suporte prioritário
- Analytics avançados

## 📚 API Documentation

### Endpoints Principais

```
# Autenticação
POST /api/v1/auth/register/
POST /api/v1/auth/login/
POST /api/v1/auth/logout/

# WhatsApp
GET  /api/v1/whatsapp/instances/
POST /api/v1/whatsapp/instances/
GET  /api/v1/whatsapp/groups/
GET  /api/v1/whatsapp/contacts/

# Agendamento
GET  /api/v1/scheduling/scheduled-messages/
POST /api/v1/scheduling/scheduled-messages/
GET  /api/v1/scheduling/templates/
POST /api/v1/scheduling/templates/

# Assinaturas
GET  /api/v1/subscriptions/plans/
POST /api/v1/subscriptions/subscribe/
GET  /api/v1/subscriptions/invoices/
```

## 🔐 Segurança

- Autenticação por token
- Rate limiting
- Validação de dados robusta
- CORS configurado
- HTTPS obrigatório em produção
- Logs de auditoria

## 🧪 Testes

```bash
# Executar todos os testes
python manage.py test

# Executar testes com cobertura
poetry run pytest --cov=apps

# Executar testes específicos
python manage.py test apps.accounts.tests
```

## 📈 Monitoramento

### Métricas importantes

- Taxa de entrega de mensagens
- Tempo de resposta da API
- Uso de recursos (CPU/Memory)
- Erros de integração WhatsApp
- Status das assinaturas

### Logs

```bash
# Ver logs em tempo real
docker-compose logs -f web

# Ver logs do worker
docker-compose logs -f worker

# Ver logs do scheduler
docker-compose logs -f scheduler
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📝 Roadmap

- [ ] App móvel (React Native)
- [ ] Integração com mais APIs de WhatsApp
- [ ] Sistema de afiliados
- [ ] Dashboard com gráficos avançados
- [ ] Integração com CRM
- [ ] Chatbot automático
- [ ] Webhooks personalizados
- [ ] API GraphQL

## 📜 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 🆘 Suporte

- 📧 Email: suporte@tsurugroups.com
- 💬 Discord: [Servidor Oficial](https://discord.gg/tsurugroups)
- 📖 Docs: [docs.tsurugroups.com](https://docs.tsurugroups.com)

## 🔗 Links Úteis

- [Demo Online](https://demo.tsurugroups.com)
- [Documentação da API](https://api.tsurugroups.com/docs)
- [Status do Sistema](https://status.tsurugroups.com)
- [Blog](https://blog.tsurugroups.com)

---

Desenvolvido com ❤️ pela equipe Tsuru Groups
