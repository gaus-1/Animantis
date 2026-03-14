"""Economy Service — financial operations between agents."""

import logging
import random

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from animantis.db.models import Agent, Clan, Transaction

logger = logging.getLogger("animantis")


# ── Errors ───────────────────────────────────────────────────


class InsufficientFundsError(Exception):
    """Agent doesn't have enough coins."""


class NotClanLeaderError(Exception):
    """Agent is not the leader of the clan."""


# ── Core ─────────────────────────────────────────────────────


async def transfer_coins(
    db: AsyncSession,
    *,
    from_agent_id: int,
    to_agent_id: int,
    amount: int,
    reason: str,
) -> Transaction:
    """Atomic coin transfer between two agents.

    Args:
        db: Database session.
        from_agent_id: Sender agent ID.
        to_agent_id: Receiver agent ID.
        amount: Amount to transfer (must be > 0).
        reason: Transaction reason (trade, donate, tax, theft, etc).

    Returns:
        Created Transaction record.

    Raises:
        InsufficientFundsError: If sender doesn't have enough coins.
        ValueError: If amount <= 0.
    """
    if amount <= 0:
        msg = "Amount must be positive"
        raise ValueError(msg)

    sender = await db.get(Agent, from_agent_id)
    receiver = await db.get(Agent, to_agent_id)

    if not sender or not receiver:
        msg = "Agent not found"
        raise ValueError(msg)

    if sender.coins < amount:
        msg = f"Agent {from_agent_id} has {sender.coins} coins, needs {amount}"
        raise InsufficientFundsError(msg)

    sender.coins -= amount
    receiver.coins += amount

    tx = Transaction(
        from_agent_id=from_agent_id,
        to_agent_id=to_agent_id,
        amount=amount,
        reason=reason,
    )
    db.add(tx)
    await db.commit()
    await db.refresh(tx)

    logger.info(
        "Transfer completed",
        extra={
            "from": from_agent_id,
            "to": to_agent_id,
            "amount": amount,
            "reason": reason,
        },
    )
    return tx


# ── Operations ───────────────────────────────────────────────


async def trade(
    db: AsyncSession,
    *,
    agent_a_id: int,
    agent_b_id: int,
    amount: int,
) -> Transaction:
    """Trade coins between two agents.

    Returns:
        Transaction record.
    """
    return await transfer_coins(
        db,
        from_agent_id=agent_a_id,
        to_agent_id=agent_b_id,
        amount=amount,
        reason="trade",
    )


async def donate(
    db: AsyncSession,
    *,
    from_agent_id: int,
    to_agent_id: int,
    amount: int,
) -> Transaction:
    """Donate coins from one agent to another.

    Returns:
        Transaction record.
    """
    return await transfer_coins(
        db,
        from_agent_id=from_agent_id,
        to_agent_id=to_agent_id,
        amount=amount,
        reason="donate",
    )


async def gamble(
    db: AsyncSession,
    *,
    agent_id: int,
    amount: int,
) -> dict:
    """Gamble coins — 50% chance to double, 50% chance to lose.

    Args:
        agent_id: Gambling agent.
        amount: Bet amount.

    Returns:
        Dict with result: {"won": bool, "amount": int, "new_balance": int}.

    Raises:
        InsufficientFundsError: If not enough coins.
    """
    if amount <= 0:
        msg = "Bet must be positive"
        raise ValueError(msg)

    agent = await db.get(Agent, agent_id)
    if not agent:
        msg = f"Agent {agent_id} not found"
        raise ValueError(msg)

    if agent.coins < amount:
        msg = f"Agent has {agent.coins} coins, bet is {amount}"
        raise InsufficientFundsError(msg)

    won = random.random() < 0.5  # noqa: S311  # nosec B311

    if won:
        agent.coins += amount
        reason = "gamble_win"
    else:
        agent.coins -= amount
        reason = "gamble_loss"

    tx = Transaction(
        from_agent_id=agent_id if not won else None,
        to_agent_id=agent_id if won else None,
        amount=amount,
        reason=reason,
    )
    db.add(tx)
    await db.commit()

    logger.info(
        "Gamble result",
        extra={"agent_id": agent_id, "won": won, "amount": amount},
    )
    return {"won": won, "amount": amount, "new_balance": agent.coins}


async def steal(
    db: AsyncSession,
    *,
    thief_id: int,
    victim_id: int,
) -> dict:
    """Attempt to steal coins — 30% success rate.

    Success: steal 10-30% of victim's coins.
    Failure: thief loses 10 reputation.

    Returns:
        Dict with result: {"success": bool, "amount": int, "reputation_change": int}.
    """
    thief = await db.get(Agent, thief_id)
    victim = await db.get(Agent, victim_id)

    if not thief or not victim:
        msg = "Agent not found"
        raise ValueError(msg)

    success = random.random() < 0.3  # noqa: S311  # nosec B311

    if success:
        steal_pct = random.uniform(0.1, 0.3)  # noqa: S311  # nosec B311
        amount = max(1, int(victim.coins * steal_pct))
        victim.coins -= amount
        thief.coins += amount
        thief.reputation -= 5

        tx = Transaction(
            from_agent_id=victim_id,
            to_agent_id=thief_id,
            amount=amount,
            reason="theft",
        )
        db.add(tx)
        await db.commit()

        logger.info(
            "Theft success",
            extra={"thief": thief_id, "victim": victim_id, "amount": amount},
        )
        return {"success": True, "amount": amount, "reputation_change": -5}

    # Failed: lose reputation
    thief.reputation -= 10
    await db.commit()

    logger.info("Theft failed", extra={"thief": thief_id, "victim": victim_id})
    return {"success": False, "amount": 0, "reputation_change": -10}


async def tax(
    db: AsyncSession,
    *,
    leader_id: int,
    clan_id: int,
    amount_per_member: int,
) -> dict:
    """Collect tax from clan members — only leader can do this.

    Args:
        leader_id: Agent ID of clan leader.
        clan_id: Clan to tax.
        amount_per_member: Amount to collect from each member.

    Returns:
        Dict with total collected and member count.

    Raises:
        NotClanLeaderError: If agent is not the leader.
    """
    clan = await db.get(Clan, clan_id)
    if not clan:
        msg = f"Clan {clan_id} not found"
        raise ValueError(msg)

    if clan.leader_agent_id != leader_id:
        msg = "Only clan leader can collect tax"
        raise NotClanLeaderError(msg)

    # Get all clan members (except leader)
    query = select(Agent).where(
        Agent.clan_id == clan_id,
        Agent.id != leader_id,
        Agent.is_alive.is_(True),
    )
    result = await db.execute(query)
    members = list(result.scalars().all())

    total_collected = 0
    for member in members:
        actual = min(amount_per_member, member.coins)
        if actual > 0:
            member.coins -= actual
            total_collected += actual

            tx = Transaction(
                from_agent_id=member.id,
                to_agent_id=leader_id,
                amount=actual,
                reason="tax",
            )
            db.add(tx)

    clan.treasury += total_collected
    await db.commit()

    logger.info(
        "Tax collected",
        extra={"clan_id": clan_id, "total": total_collected, "members": len(members)},
    )
    return {"total_collected": total_collected, "members_taxed": len(members)}


async def invest(
    db: AsyncSession,
    *,
    agent_id: int,
    zone_id: int,
    amount: int,
) -> Transaction:
    """Invest coins in a zone — increases zone population.

    Returns:
        Transaction record.

    Raises:
        InsufficientFundsError: If not enough coins.
    """
    from animantis.db.models import Zone

    if amount <= 0:
        msg = "Investment must be positive"
        raise ValueError(msg)

    agent = await db.get(Agent, agent_id)
    zone = await db.get(Zone, zone_id)

    if not agent or not zone:
        msg = "Agent or zone not found"
        raise ValueError(msg)

    if agent.coins < amount:
        msg = f"Agent has {agent.coins} coins, needs {amount}"
        raise InsufficientFundsError(msg)

    agent.coins -= amount
    zone.population += 1
    agent.reputation += 2

    tx = Transaction(
        from_agent_id=agent_id,
        to_agent_id=None,
        amount=amount,
        reason=f"invest_zone_{zone_id}",
    )
    db.add(tx)
    await db.commit()
    await db.refresh(tx)

    logger.info(
        "Investment made",
        extra={"agent_id": agent_id, "zone_id": zone_id, "amount": amount},
    )
    return tx


# ── Queries ──────────────────────────────────────────────────


async def get_agent_transactions(
    db: AsyncSession,
    *,
    agent_id: int,
    limit: int = 50,
) -> list[Transaction]:
    """Get transaction history for an agent."""
    from sqlalchemy import or_

    query = (
        select(Transaction)
        .where(
            or_(
                Transaction.from_agent_id == agent_id,
                Transaction.to_agent_id == agent_id,
            )
        )
        .order_by(Transaction.created_at.desc())
        .limit(min(limit, 100))
    )
    result = await db.execute(query)
    return list(result.scalars().all())
