import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Database connection
engine = None

def get_engine():
    global engine
    
    if engine is None:
        # Direct connection with password
        connection_string = "postgresql+psycopg2://ass_db:npg_Y0wuLVX3TUPJ@ep-withered-hat-d857qrwn.database.us-east-2.cloud.databricks.com:5432/databricks_postgres?sslmode=require"
        engine = create_engine(
            connection_string,
            pool_pre_ping=True,
            pool_recycle=3600
        )
    
    return engine

# Database models
Base = declarative_base()

class Ticket(Base):
    __tablename__ = 'tickets'
    __table_args__ = {'schema': 'support_db', 'extend_existing': True}
    
    ticket_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default='open')
    created_by = Column(String(100), nullable=False, default='System')
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    messages = relationship('Message', back_populates='ticket', cascade='all, delete-orphan', foreign_keys='Message.ticket_id')

class Message(Base):
    __tablename__ = 'ticket_messages'
    __table_args__ = {'schema': 'support_db', 'extend_existing': True}
    
    message_id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey('support_db.tickets.ticket_id'), nullable=False)
    message_text = Column(Text, nullable=False)
    author = Column(String(100), nullable=False, default='User')
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    ticket = relationship('Ticket', back_populates='messages', foreign_keys=[ticket_id])

# Initialize database (tables already exist, so we just need to map to them)
def init_db():
    # Tables already exist in the database, no need to create
    pass

# Database session
def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()

# Initialize the database
init_db()

# Streamlit App
st.set_page_config(page_title="Support Ticket Manager", page_icon="🎫", layout="wide")

st.title("🎫 Support Ticket Manager")
st.markdown("---")

# Sidebar navigation
page = st.sidebar.radio("Navigation", ["View Tickets", "Create Ticket"])

if page == "View Tickets":
    st.header("All Support Tickets")
    
    # Get all tickets
    session = get_session()
    try:
        tickets = session.query(Ticket).order_by(Ticket.created_at.desc()).all()
        
        if not tickets:
            st.info("No tickets found. Create your first ticket!")
        else:
            # Display tickets in a grid
            for ticket in tickets:
                with st.expander(f"#{ticket.ticket_id} - {ticket.title} [{ticket.status.upper()}]"):
                    st.markdown(f"**Created By:** {ticket.created_by}")
                    st.markdown(f"**Created:** {ticket.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                    st.markdown(f"**Status:** {ticket.status}")
                    
                    # Update status
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        new_status = st.selectbox(
                            f"Update Status for Ticket #{ticket.ticket_id}",
                            ["open", "in_progress", "resolved", "closed"],
                            index=["open", "in_progress", "resolved", "closed"].index(ticket.status),
                            key=f"status_{ticket.ticket_id}"
                        )
                    with col2:
                        if st.button("Update", key=f"update_{ticket.ticket_id}"):
                            ticket.status = new_status
                            session.commit()
                            st.success(f"Status updated to {new_status}!")
                            st.rerun()
                    
                    st.markdown("---")
                    st.subheader("Messages")
                    
                    # Display messages
                    messages = session.query(Message).filter_by(ticket_id=ticket.ticket_id).order_by(Message.created_at).all()
                    
                    if messages:
                        for msg in messages:
                            st.markdown(f"**{msg.author}** ({msg.created_at.strftime('%Y-%m-%d %H:%M:%S')}):")
                            st.markdown(f"> {msg.message_text}")
                    else:
                        st.info("No messages yet.")
                    
                    # Add new message
                    st.markdown("**Add a Message:**")
                    with st.form(key=f"message_form_{ticket.ticket_id}"):
                        message_text = st.text_area("Message", key=f"msg_text_{ticket.ticket_id}")
                        author_name = st.text_input("Your Name", value="User", key=f"author_{ticket.ticket_id}")
                        submit_message = st.form_submit_button("Add Message")
                        
                        if submit_message and message_text:
                            new_message = Message(
                                ticket_id=ticket.ticket_id,
                                message_text=message_text,
                                author=author_name
                            )
                            session.add(new_message)
                            session.commit()
                            st.success("Message added!")
                            st.rerun()
    finally:
        session.close()

elif page == "Create Ticket":
    st.header("Create New Support Ticket")
    
    with st.form(key="create_ticket_form"):
        title = st.text_input("Title", placeholder="Brief description of the issue")
        created_by = st.text_input("Your Name", value="User", placeholder="Who is creating this ticket?")
        initial_status = st.selectbox("Initial Status", ["open", "in_progress"])
        
        submit_button = st.form_submit_button("Create Ticket")
        
        if submit_button:
            if not title:
                st.error("Title is required!")
            elif not created_by:
                st.error("Your name is required!")
            else:
                session = get_session()
                try:
                    new_ticket = Ticket(
                        title=title,
                        created_by=created_by,
                        status=initial_status
                    )
                    session.add(new_ticket)
                    session.commit()
                    st.success(f"Ticket #{new_ticket.ticket_id} created successfully!")
                    st.balloons()
                finally:
                    session.close()

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info("This app manages support tickets with Lakebase (Postgres) backend.")
