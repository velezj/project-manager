{% import 'variables' as variables %}

export BASTION=`terraform output bastion-ip`
export NAT=`terraform output nat-ip`
export SALT_MASTER="10.0.0.10"


alias ssh-salt-master="ssh -i {{ variables.devops_key }} -o ProxyCommand=\"ssh -i {{ variables.devops_key }} -W %h:%p ubuntu@${BASTION}\" ubuntu@${SALT_MASTER}"

{% for i in range( variables.number_of_minions ) %}
export SALT_MINION{{ i }}="10.0.0.{{ 20 + i }}"
alias ssh-salt-minion{{ i }}="ssh -i {{ variables.devops_key }} -o ProxyCommand=\"ssh -i {{ variables.devops_key }} -W %h:%p ubuntu@${BASTION}\" ubuntu@${SALT_MINION{{ i }}}"
{% endfor %}
